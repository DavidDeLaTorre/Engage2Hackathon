
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

    The KML file will contain one Placemark per flight (identified by "icao24"),
    each with a LineString representing the trajectory using the fields:
    "icao24", "altitude", "lat_deg", "lon_deg".

    Args:
        df (pd.DataFrame): The DataFrame containing the flight data.
        output_file (str): The file path for the output KML file.
    """
    # Ensure the necessary columns exist.
    required_columns = {'icao24', 'altitude', 'lat_deg', 'lon_deg'}
    if not required_columns.issubset(df.columns):
        print("Error: The DataFrame does not contain all required columns for KML export.")
        sys.exit(1)

    # Group the data by 'icao24' so each flight gets its own placemark.
    grouped = df.groupby('icao24')

    # Define a list of arbitrary colors for the lines.
    num_flights = len(grouped)  # Assume 'grouped' is your groupby object for flights.
    # KML uses aabbggrr format (alpha, blue, green, red). Colors are chosen arbitrarily.
    colors = generate_kml_colors(num_flights)

    # Arbitrary width for all lines
    line_width = 4

    # Start building the KML content.
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
"""
    for idx, (aircraft_id, group) in enumerate(grouped):

        # Select a color from the list (cycle through if there are more flights than colors).
        color = colors[idx % len(colors)]

        # Sort the group by the timestamp field 'ts' (epoch in milliseconds)
        group = group.sort_values('ts')

        placemark = f"""    <!-- Placemark for flight {aircraft_id} -->
    <Placemark>
      <name>Flight Trajectory - {aircraft_id}</name>
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
        # Append the coordinates from the flight. KML requires lon,lat,alt.
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
