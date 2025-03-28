#!/usr/bin/env python3
"""
This script processes ADS-B data stored in a parquet file.
It performs the following tasks:
1. Loads the parquet file into a pandas DataFrame.
2. Filters the DataFrame for a specific aircraft using its unique "icao24" identifier.
3. Removes rows where the "altitude" field is null.
4. Saves the filtered DataFrame to a CSV file.

Usage:
    python process_adsb.py <input_parquet_file> <icao24_value> <output_csv_file>
"""

import sys

from tools_import import load_and_process_parquet_files
from tools_export import export_trajectories_to_csv, export_trajectories_to_kml


def main():
    # Ensure that the correct number of arguments are provided.
    if len(sys.argv) != 4:
        input_file = "data/engage-hackathon-2025/year=2024/month=11/day=16/hour=12/"
        input_file += "1225667186084f958614500e99a47e92.snappy.parquet"
        icao24 = "01024c"
        output_csv = "output/test_single_01024c_landing.csv"
        output_kml = "output/test_single_01024c_landing.kml"
    else:  # Unpack command line arguments
        input_file = sys.argv[1]
        icao24 = sys.argv[2]
        output_csv = sys.argv[3]
        output_kml = sys.argv[3]

    # Process the ADS-B data.
    filtered_df = load_and_process_parquet_files(
        file_list=[input_file],
        icao24_list=[icao24],
        columns_to_clean=['lat_deg', 'lon_deg'],
        columns_to_extract=['df', 'icao24', 'ts', 'altitude', 'lat_deg', 'lon_deg']
    )

    # Save the filtered DataFrame to CSV.
    export_trajectories_to_csv(filtered_df, output_csv)

    # Export the trajectory to a KML file.
    export_trajectories_to_kml(filtered_df, output_kml)


if __name__ == '__main__':
    main()
