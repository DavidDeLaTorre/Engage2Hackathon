#!/usr/bin/env python3
"""
This script processes ADS-B data stored in a parquet file.
It performs the following tasks:
1. Loads the parquet file into a pandas DataFrame.
2. Optionally filters the DataFrame for one or more aircraft using their "icao24" identifiers.
   If no identifiers are provided, it processes all flights in the dataset.
3. Removes rows where the "altitude" field is null.
4. Saves the resulting data to a CSV file.
5. Exports the flight trajectories as a KML file. In the KML,
   each flight (icao24) gets its own Placemark with a LineString representing its trajectory,
   and an arbitrary color is assigned to the line.

Usage:
    # Process all flights (default)
    python process_adsb.py <input_parquet_file> <output_csv_file> <output_kml_file>

    # Process only specific flights (e.g., two flights)
    python process_adsb.py <input_parquet_file> <output_csv_file> <output_kml_file> icao24_A icao24_B
"""

import sys

from tools_import import process_adsb_data
from tools_export import save_to_csv, export_trajectories_to_kml


def main():
    """
    Main function to process ADS-B data, filter by provided flights (if any),
    and export the results to CSV and KML files.

    Command-line arguments:
        <input_parquet_file> <output_csv_file> <output_kml_file> [icao24_1 icao24_2 ...]
    """
    if len(sys.argv) < 4:
        print(
            "Usage: python process_adsb.py <input_parquet_file> <output_csv_file> <output_kml_file> [icao24_1 icao24_2 ...]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_csv = sys.argv[2]
    output_kml = sys.argv[3]

    input_file = "data/engage-hackathon-2025/year=2024/month=11/day=16/hour=0/45f63f420e6e4985bbb2e9b2e976a782.snappy.parquet"
    output_csv = "output/lacacadelavaca2.csv"
    output_kml = "output/lacacadelavaca2.kml"

    # Optional flight identifiers provided as extra command-line arguments.
    icao24_list = sys.argv[4:] if len(sys.argv) > 4 else None

    # Process ADS-B data.
    filtered_df = process_adsb_data(input_file, icao24_list)

    # Save the filtered DataFrame to CSV.
    save_to_csv(filtered_df, output_csv)

    # Export the trajectories to a KML file.
    export_trajectories_to_kml(filtered_df, output_kml)


if __name__ == '__main__':
    main()
