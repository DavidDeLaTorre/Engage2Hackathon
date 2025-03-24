
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
    Exports the flight trajectories to a KML file, splitting each flight's trajectory
    into separate segments based on a precomputed "segment" column. Each segment is exported
    as an individual Placemark.

    The KML file will contain one Placemark per segment (grouped by "icao24" and "segment"),
    with a LineString representing the trajectory using the fields: "icao24", "altitude",
    "lat_deg", "lon_deg". If the DataFrame contains a "trajectory" column (e.g., 'landing',
    'departing', or 'level'), it will be included in the placemark name.

    Args:
        df (pd.DataFrame): The DataFrame containing the flight data. Must include the columns:
                           'icao24', 'altitude', 'lat_deg', 'lon_deg', and 'segment'. Optionally,
                           it may include 'ts' for sorting and 'trajectory' for classification.
        output_file (str): The file path for the output KML file.
    """
    # Ensure the necessary columns exist.
    required_columns = {'icao24', 'altitude', 'lat_deg', 'lon_deg', 'segment'}
    if not required_columns.issubset(df.columns):
        print("Error: The DataFrame does not contain all required columns for KML export.")
        sys.exit(1)

    # If a timestamp is available, sort by it. Otherwise, sort by segment.
    sort_column = 'ts' if 'ts' in df.columns else 'segment'
    df = df.sort_values(sort_column)

    # Group the data by 'icao24' and 'segment' so that each segment gets its own placemark.
    grouped = df.groupby(['icao24', 'segment'])

    # Count the total number of segments to generate colors accordingly.
    num_segments = len(grouped)
    colors = generate_kml_colors(num_segments)  # generate_kml_colors should produce valid KML colors.
    line_width = 4  # Arbitrary width for all lines

    # Start building the KML content.
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
"""
    for idx, ((aircraft_id, segment_id), group) in enumerate(grouped):
        # Cycle through colors if necessary.
        color = colors[idx % len(colors)]
        # Sort each segment by timestamp if available.
        if 'ts' in group.columns:
            group = group.sort_values('ts')

        # If trajectory classification is available, include it.
        traj_class = group['trajectory'].iloc[0] if 'trajectory' in group.columns else "N/A"

        placemark = f"""    <!-- Placemark for flight {aircraft_id}, segment {segment_id} -->
    <Placemark>
      <name>Flight {aircraft_id} - Segment {segment_id} ({traj_class})</name>
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
        # Append coordinates (KML requires lon,lat,alt).
        for _, row in group.iterrows():
            placemark += f"          {row['lon_deg']},{row['lat_deg']},{row['altitude']}\n"
        placemark += """        </coordinates>
      </LineString>
    </Placemark>
"""
        kml_content += placemark

    # Close the Document and KML tags.
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
