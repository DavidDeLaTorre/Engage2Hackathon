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

from tools_calculate import compute_segment_delta_times, plot_delta_time_pdf, compute_delta_time_statistics, \
    plot_delta_time_pdf_by_runway, find_outliers
from tools_export import export_trajectories_to_csv, export_trajectories_to_kml
from tools_filter import identify_segments, sort_dataframe, filter_dataframe_by_bounds, filter_dataframe_by_altitude, \
    clean_dataframe_nulls, extract_adsb_columns, identify_landing_runway
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
    output_name = 'output/test_1week'

    # Define a cache file path (adjust folder as needed)
    cache_file = f"output/test_1week_cached_df_{year}_{month:02d}_{day:02d}.pkl"

    # If the cache file exists, load the dataframe from it.
    if os.path.exists(cache_file):
        print(f"Loading cached dataframe from {cache_file} ...")
        df = pd.read_pickle(cache_file)
    else:
        print("Cache file not found. Processing data ...")

        # For one entire day, process all hours from 0 to 23
        df = load_parquet_files(
            year, month, day, 0,
            year, month, day+7, 23,
            base_path="data/engage-hackathon-2025")

        if df.empty:
            print("No data found for the specified day.")
            sys.exit(1)

        # Save the dataframe to cache for future runs
        print(f"Saving processed dataframe to cache file {cache_file} ...")
        df.to_pickle(cache_file)


    # Define a cache file path (adjust folder as needed)
    cache_file2 = f"output/test_1week_cached2_df_{year}_{month:02d}_{day:02d}.pkl"

    # If the cache file exists, load the dataframe from it.
    if os.path.exists(cache_file2):
        print(f"Loading cached dataframe2 from {cache_file2} ...")
        df = pd.read_pickle(cache_file2)
    else:
        print("Cache file2 not found. Processing data ...")

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

        # Save the dataframe to cache for future runs
        print(f"Saving processed dataframe to cache file2 {cache_file2} ...")
        df.to_pickle(cache_file2)

    # Identify and extract landings, with caching
    cache_file3 = f"output/test_1week_cached_landing_{year}_{month:02d}_{day:02d}.pkl"
    if os.path.exists(cache_file3):
        print(f"Loading cached landing runway results from {cache_file3} ...")
        df_with_runway, basic_info_df, df_segments_ils = pd.read_pickle(cache_file3)
    else:
        print("Cache file for landing runway not found. Processing landing runway results ...")
        df_with_runway, basic_info_df, df_segments_ils = identify_landing_runway(df)

        print(f"Saving landing runway results to cache file {cache_file3} ...")
        pd.to_pickle((df_with_runway, basic_info_df, df_segments_ils), cache_file3)

    # Define the normal range thresholds (in seconds)
    min_delta = 100
    max_delta = 500

    # Filter the dataframe to only include segments with delta_time within the normal range
    normal_basic_info_df = basic_info_df[
        (basic_info_df['delta_time'] >= min_delta) & (basic_info_df['delta_time'] <= max_delta)]

    # Compute statistics
    stats = compute_delta_time_statistics(normal_basic_info_df)

    # Compute statistics for each runway by grouping basic_info_df on 'nearest_runway'
    stats_by_runway = {}
    for runway, runway_df in normal_basic_info_df.groupby('runway_fap'):
        stats_by_runway[runway] = compute_delta_time_statistics(runway_df)
        print(f"Statistics for Runway {runway}:")
        for stat_name, value in stats_by_runway[runway].items():
            print(f"  {stat_name}: {value}")
        print()

    # Filter the dataframe to only include segments with delta_time within the normal range
    normal_df_with_runway = df_with_runway[
        (df_with_runway['delta_time'] >= min_delta) & (df_with_runway['delta_time'] <= max_delta)]
    # Extract the delta_time for each icao24 and landing and segment
    df_times = compute_segment_delta_times(normal_df_with_runway)
    plot_delta_time_pdf(df_times)

    # Filter the dataframe to only include segments with delta_time within the normal range
    normal_df_segments_ils = df_segments_ils[
        (df_segments_ils['delta_time'] >= min_delta) & (df_segments_ils['delta_time'] <= max_delta)]
    # Extract the delta_time for each icao24 and landing and segment
    df_times = compute_segment_delta_times(normal_df_segments_ils)
    plot_delta_time_pdf(df_times)

    # Call the plotting function
    plot_delta_time_pdf_by_runway(normal_basic_info_df)
    find_outliers(basic_info_df)

    # # Save the filtered DataFrame to CSV & KML
    # print("export_trajectories_to_csv all ...")
    # export_trajectories_to_csv(df, output_name + '_all.csv')
    # print("export_trajectories_to_kml all ...")
    # export_trajectories_to_kml(df, output_name + '_all.kml')
    # print("export_trajectories_to_kml segments ...")
    # export_trajectories_to_kml(df_segments_ils, output_name + '_segments_all.kml')
    # export_trajectories_to_kml(normal_df_segments_ils, output_name + '_segments_all_filtered.kml')


if __name__ == '__main__':
    main()
