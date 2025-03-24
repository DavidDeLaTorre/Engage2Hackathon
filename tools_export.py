
import sys
import pandas as pd
from matplotlib import pyplot as plt


def generate_kml_colors(num_colors: int) -> list:
    """
    Generate a "jet-like" colormap with num_colors different colors.
    Each color is returned in KML's aabbggrr hex format.

    Args:
        num_colors (int): Number of distinct colors required.

    Returns:
        list: A list of color strings in aabbggrr format.
    """
    cmap = plt.get_cmap('jet')
    colors = []
    for i in range(num_colors):
        # Normalize the index and get the RGBA values from the colormap.
        normalized = i / (num_colors - 1) if num_colors > 1 else 0
        r, g, b, a = cmap(normalized)
        # Convert float RGBA (0-1) to integers (0-255)
        r_int = int(r * 255)
        g_int = int(g * 255)
        b_int = int(b * 255)
        a_int = int(a * 255)
        # Format into KML's aabbggrr hex format.
        kml_color = f"{a_int:02x}{b_int:02x}{g_int:02x}{r_int:02x}"
        colors.append(kml_color)
    return colors


def export_trajectories_to_csv(df: pd.DataFrame, output_file: str):
    """
    Save the provided DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): The DataFrame to save.
        output_file (str): The file path for the output CSV.
    """
    try:
        df.to_csv(output_file, index=False)
        print(f"Filtered data saved to {output_file}")
    except Exception as e:
        print(f"Error writing CSV file: {e}")
        sys.exit(1)


def export_trajectories_to_kml(df: pd.DataFrame, output_file: str):
    """
    Exports the flight trajectories to a KML file.

    If the DataFrame contains a "segment" column, the trajectories are split by segment,
    with each segment exported as its own Placemark (grouped by "icao24" and "segment").
    If the DataFrame does not contain "segment", all points for each aircraft (grouped by "icao24")
    are exported as a single Placemark.

    The KML file uses the columns:
      - "icao24", "altitude", "lat_deg", "lon_deg", and optionally "ts" for sorting.
      - If available, a "trajectory" column (e.g., 'landing', 'departing', 'level') is used in the placemark name.

    Args:
        df (pd.DataFrame): DataFrame containing the flight data.
        output_file (str): The file path for the output KML file.
    """
    # Validate required columns
    required_columns = {'icao24', 'altitude', 'lat_deg', 'lon_deg'}
    if not required_columns.issubset(df.columns):
        print("Error: The DataFrame does not contain all required columns for KML export.")
        sys.exit(1)

    # Check if the DataFrame has segmentation information.
    has_segments = 'segment' in df.columns

    # Use 'ts' (if available) for sorting; otherwise use 'segment' (if available)
    if 'ts' in df.columns:
        df = df.sort_values('ts')
    elif has_segments:
        df = df.sort_values('segment')

    # Define grouping:
    # If segments exist, group by both 'icao24' and 'segment'; otherwise, group by 'icao24' only.
    if has_segments:
        group_keys = ['icao24', 'segment']
    else:
        group_keys = ['icao24']

    grouped = df.groupby(group_keys)

    # Count the total number of groups to generate colors.
    num_groups = len(grouped)
    colors = generate_kml_colors(num_groups)  # This helper function must return valid KML color strings.
    line_width = 4  # Arbitrary line width

    # Start building KML content.
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
"""
    for idx, group_keys_val in enumerate(grouped.groups):
        # For single-key grouping, group_keys_val is just the aircraft id.
        # For two-key grouping, it is a tuple (icao24, segment).
        if has_segments:
            aircraft_id, segment_id = group_keys_val
        else:
            aircraft_id = group_keys_val
            segment_id = None

        group = grouped.get_group(group_keys_val)

        # If a timestamp is available, sort the group.
        if 'ts' in group.columns:
            group = group.sort_values('ts')

        # Retrieve trajectory classification if available.
        if 'trajectory' in group.columns:
            traj_class = group['trajectory'].iloc[0]
        else:
            traj_class = "N/A"

        # Build the placemark name based on available keys.
        if segment_id is not None:
            placemark_name = f"Flight {aircraft_id} - Segment {segment_id} ({traj_class})"
        else:
            placemark_name = f"Flight {aircraft_id} ({traj_class})"

        # Select a color (cycle if necessary).
        color = colors[idx % len(colors)]

        placemark = f"""    <!-- Placemark for {placemark_name} -->
    <Placemark>
      <name>{placemark_name}</name>
      <Style>
        <LineStyle>
          <color>{color}</color>
          <width>{line_width}</width>
        </LineStyle>
      </Style>
      <LineString>
        <!-- Coordinates: longitude,latitude,altitude -->
        <coordinates>
"""
        # Append the coordinates (KML expects lon,lat,alt).
        for _, row in group.iterrows():
            placemark += f"          {row['lon_deg']},{row['lat_deg']},{row['altitude']}\n"
        placemark += """        </coordinates>
      </LineString>
    </Placemark>
"""
        kml_content += placemark

    # Close KML tags.
    kml_content += """  </Document>
</kml>
"""
    # Write the KML content to the output file.
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(kml_content)
        print(f"KML file saved to {output_file}")
    except Exception as e:
        print(f"Error writing KML file: {e}")
        sys.exit(1)


def export_trajectories_FAP_predicted_FAP_to_kml(df: pd.DataFrame, output_file: str, FAP_position: dict, nearest_fap_info: dict):
    """
    Exports the flight trajectories to a KML file.

    If the DataFrame contains a "segment" column, the trajectories are split by segment,
    with each segment exported as its own Placemark (grouped by "icao24" and "segment").
    If the DataFrame does not contain "segment", all points for each aircraft (grouped by "icao24")
    are exported as a single Placemark.

    It also plots the nearest FAP point and the FAP position of all runways

    The KML file uses the columns:
      - "icao24", "altitude", "lat_deg", "lon_deg", and optionally "ts" for sorting.
      - If available, a "trajectory" column (e.g., 'landing', 'departing', 'level') is used in the placemark name.

    Args:
        df (pd.DataFrame): DataFrame containing the flight data.
        output_file (str): The file path for the output KML file.
    """
    # Validate required columns
    required_columns = {'icao24', 'altitude', 'lat_deg', 'lon_deg'}
    if not required_columns.issubset(df.columns):
        print("Error: The DataFrame does not contain all required columns for KML export.")
        sys.exit(1)

    # Check if the DataFrame has segmentation information.
    has_segments = 'segment' in df.columns

    # Use 'ts' (if available) for sorting; otherwise use 'segment' (if available)
    if 'ts' in df.columns:
        df = df.sort_values('ts')
    elif has_segments:
        df = df.sort_values('segment')

    # Define grouping:
    # If segments exist, group by both 'icao24' and 'segment'; otherwise, group by 'icao24' only.
    if has_segments:
        group_keys = ['icao24', 'segment']
    else:
        group_keys = ['icao24']

    grouped = df.groupby(group_keys)

    # Count the total number of groups to generate colors.
    num_groups = len(grouped)
    colors = generate_kml_colors(num_groups)  # This helper function must return valid KML color strings.
    line_width = 4  # Arbitrary line width

    # Start building KML content.
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
"""
    for idx, group_keys_val in enumerate(grouped.groups):
        # For single-key grouping, group_keys_val is just the aircraft id.
        # For two-key grouping, it is a tuple (icao24, segment).
        if has_segments:
            aircraft_id, segment_id = group_keys_val
        else:
            aircraft_id = group_keys_val
            segment_id = None

        group = grouped.get_group(group_keys_val)

        # If a timestamp is available, sort the group.
        if 'ts' in group.columns:
            group = group.sort_values('ts')

        # Retrieve trajectory classification if available.
        if 'trajectory' in group.columns:
            traj_class = group['trajectory'].iloc[0]
        else:
            traj_class = "N/A"

        # Build the placemark name based on available keys.
        if segment_id is not None:
            placemark_name = f"Flight {aircraft_id} - Segment {segment_id} ({traj_class})"
        else:
            placemark_name = f"Flight {aircraft_id} ({traj_class})"

        # Select a color (cycle if necessary).
        color = colors[idx % len(colors)]

        placemark = f"""    <!-- Placemark for {placemark_name} -->
    <Placemark>
      <name>{placemark_name}</name>
      <Style>
        <LineStyle>
          <color>{color}</color>
          <width>{line_width}</width>
        </LineStyle>
      </Style>
      <LineString>
        <!-- Coordinates: longitude,latitude,altitude -->
        <coordinates>
"""
        # Append the coordinates (KML expects lon,lat,alt).
        for _, row in group.iterrows():
            placemark += f"          {row['lon_deg']},{row['lat_deg']},{row['altitude']}\n"
        placemark += """        </coordinates>
      </LineString>
    </Placemark>
"""

        # Add FAP point placemarks
    for runway, fap in FAP_position.items():
        kml_content += f"""    <!-- FAP for Runway {runway} -->
    <Placemark>
      <name>FAP Runway {runway}</name>
      <Style>
        <IconStyle>
          <color>ff0000ff</color> <!-- Red -->
          <scale>1.2</scale>
        </IconStyle>
      </Style>
      <Point>
        <coordinates>{fap.longitude},{fap.latitude},{fap.altitude}</coordinates>
      </Point>
    </Placemark>
"""

    # Add nearest point placemark
    point = nearest_fap_info['point']
    kml_content += f"""    <!-- Nearest point to FAP -->
    <Placemark>
      <name>Nearest Point to FAP {nearest_fap_info['runway']}</name>
      <Style>
        <IconStyle>
          <color>ff00ffff</color> <!-- Yellow -->
          <scale>1.1</scale>
        </IconStyle>
      </Style>
      <Point>
        <coordinates>{point['lon_deg']},{point['lat_deg']},{point['altitude']}</coordinates>
      </Point>
    </Placemark>
"""

    kml_content += placemark

    # Close KML tags.
    kml_content += """  </Document>
</kml>
"""
    # Write the KML content to the output file.
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(kml_content)
        print(f"KML file saved to {output_file}")
    except Exception as e:
        print(f"Error writing KML file: {e}")
        sys.exit(1)

