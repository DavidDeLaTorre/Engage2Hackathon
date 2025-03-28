#!/usr/bin/env python3
"""
Main script to generate a KML with all flights for one entire day.
This script imports functions from tools_load_many.py and tools_misc.py.
Usage:
    python main_generate_kml.py <year> <month> <day> <output_kml_file>
Example:
    python main_generate_kml.py 2024 11 16 output.kml
"""
import os
import sys

import pandas as pd

from tools_filter import filter_dataframe_by_bounds, filter_dataframe_by_altitude, sort_dataframe
from tools_import import load_parquet_files
from tools_export import export_trajectories_to_kml, export_trajectories_to_csv


def main():
    if len(sys.argv) != 6:
        print("Usage: python main_generate_kml.py <year> <month> <day> <output_csv_file> <output_kml_file>")
        sys.exit(1)

    year = int(sys.argv[1])
    month = int(sys.argv[2])
    day = int(sys.argv[3])
    output_csv = sys.argv[4]
    output_kml = sys.argv[5]

    # Define a cache file path (adjust folder as needed)
    cache_file = f"output/main_generate_kml_cached_df_{year}_{month:02d}_{day:02d}.pkl"

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

        # Filter dataframe by geographical coordinates around Madrid
        min_lat, max_lat, min_lon, max_lon = [40.3, 40.8, -3.8, -3.3]  # [deg]
        df = filter_dataframe_by_bounds(df, min_lat, max_lat, min_lon, max_lon)
        min_alt, max_alt = [0, 4000]  # [ft]
        df = filter_dataframe_by_altitude(df, min_alt, max_alt)

        # Sort dataframe by icao24 and time
        df = sort_dataframe(df)

        # Save the dataframe to cache for future runs
        print(f"Saving processed dataframe to cache file {cache_file} ...")
        df.to_pickle(cache_file)

    # Export dataframe to CSV
    export_trajectories_to_csv(df, output_csv)

    # Generate the KML with all flights
    export_trajectories_to_kml(df, output_kml)


if __name__ == '__main__':
    main()
