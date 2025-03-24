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

from tools_export import export_trajectories_to_csv, export_trajectories_to_kml
from tools_filter import identify_segments, sort_dataframe, filter_dataframe_by_bounds, filter_dataframe_by_altitude
from tools_import import load_and_process_parquet_files


def main():
    """
    Main function to process ADS-B data, filter by provided flights (if any),
    and export the results to CSV and KML files.

    Command-line arguments:
        <input_parquet_file> <output_csv_file> <output_kml_file> [icao24_1 icao24_2 ...]
    """

    # Inputs
    input_file1 = "data/engage-hackathon-2025/year=2024/month=11/day=16/hour=13/"
    input_file1 += "9e6479c5cdd0497684fe6d961b61f53d.snappy.parquet"
    input_file2 = "data/engage-hackathon-2025/year=2024/month=11/day=16/hour=12/"
    input_file2 += "1225667186084f958614500e99a47e92.snappy.parquet"

    output_csv = "output/multi_segments.csv"
    output_kml = "output/multi_segments.kml"


    # Optional flight identifiers provided as extra command-line arguments.
    icao24_list = sys.argv[4:] if len(sys.argv) > 4 else None

    # Process ADS-B data.
    filtered_df = load_and_process_parquet_files([input_file1, input_file2], icao24_list)

    # Sort dataframe by ICAO24 and time
    sorted_df = sort_dataframe(filtered_df)

    # Identify landing/departure segments, for each icao24 flight
    df_segments, df_extra = identify_segments(sorted_df)

    # Final df
    df = df_segments

    # Filter dataframe by geographical coordinates around Madrid
    min_lat, max_lat, min_lon, max_lon = [40.3, 40.8, -3.8, -3.3]  # [deg]
    df = filter_dataframe_by_bounds(df, min_lat, max_lat, min_lon, max_lon)
    min_alt, max_alt = [-1000, 10000]  # [ft]
    df = filter_dataframe_by_altitude(df, min_alt, max_alt)

    # Save the filtered DataFrame to CSV
    export_trajectories_to_csv(df, output_csv)

    # Export the trajectories to a KML file.
    export_trajectories_to_kml(df, output_kml)


if __name__ == '__main__':
    main()
