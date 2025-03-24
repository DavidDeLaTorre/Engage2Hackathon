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
import os
import sys

import pandas as pd

from tools_export import export_trajectories_to_csv, export_trajectories_to_kml
from tools_filter import identify_segments, sort_dataframe, filter_dataframe_by_bounds, filter_dataframe_by_altitude, \
    clean_dataframe_nulls, extract_adsb_columns
from tools_import import load_and_process_parquet_files, load_parquet_files


def main():
    """
    Main function to process ADS-B data, filter by provided flights (if any),
    and export the results to CSV and KML files.

    Command-line arguments:
        <input_parquet_file> <output_csv_file> <output_kml_file> [icao24_1 icao24_2 ...]
    """

    year = 2024
    month = 11
    day = 16
    output_csv = 'output/test_1day.csv'
    output_kml = 'output/test_1day.kml'

    # Define a cache file path (adjust folder as needed)
    cache_file = f"output/test_1day_cached_df_{year}_{month:02d}_{day:02d}.pkl"

    # Optional flight identifiers provided as extra command-line arguments.
    icao24_list = sys.argv[4:] if len(sys.argv) > 4 else None

    # If the cache file exists, load the dataframe from it.
    if os.path.exists(cache_file):
        print(f"Loading cached dataframe from {cache_file} ...")
        df = pd.read_pickle(cache_file)
    else:
        print("Cache file not found. Processing data ...")

        # For one entire day, process all hours from 0 to 23
        df = load_parquet_files(
            year, month, day, 0,
            year, month, day, 23,
            base_path="data/engage-hackathon-2025")

        if df.empty:
            print("No data found for the specified day.")
            sys.exit(1)

        # Save the dataframe to cache for future runs
        print(f"Saving processed dataframe to cache file {cache_file} ...")
        df.to_pickle(cache_file)

    # Filter the data to remove null altitude/lat_deg.
    print("clean_dataframe_nulls ...")
    columns_to_clean = ['altitude', 'lat_deg']
    df_filtered = clean_dataframe_nulls(df, columns_to_clean)

    # Extract the required subset of columns.
    print("extract_adsb_columns ...")
    columns_to_extract = None
    df_extracted = extract_adsb_columns(df_filtered, columns_to_extract)

    # Sort dataframe by ICAO24 and time
    print("sort_dataframe ...")
    sorted_df = sort_dataframe(df_extracted)

    # Identify landing/departure segments, for each icao24 flight
    print("identify_segments ...")
    df_segments, df_extra = identify_segments(sorted_df)

    # Final df
    df = df_segments

    # Filter dataframe by geographical coordinates around Madrid
    print("filter_dataframe_by_bounds ...")
    min_lat, max_lat, min_lon, max_lon = [40.3, 40.8, -3.8, -3.3]  # [deg]
    df = filter_dataframe_by_bounds(df, min_lat, max_lat, min_lon, max_lon)
    min_alt, max_alt = [-1000, 10000]  # [ft]
    df = filter_dataframe_by_altitude(df, min_alt, max_alt)

    # Save the filtered DataFrame to CSV & KML
    print("export_trajectories_to_xxx ...")
    export_trajectories_to_csv(df, output_csv)
    export_trajectories_to_kml(df, output_kml)


if __name__ == '__main__':
    main()
