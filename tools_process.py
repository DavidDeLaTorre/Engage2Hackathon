import os
import sys
from datetime import date, timedelta

import pandas as pd

from tools_calculate import (
    compute_segment_delta_times,
    plot_delta_time_pdf,
    compute_delta_time_statistics,
    plot_delta_time_pdf_by_runway, get_day_of_week
)
from tools_export import (
    export_trajectories_to_csv,
    export_trajectories_to_kml
)
from tools_filter import (
    identify_segments,
    sort_dataframe,
    filter_dataframe_by_bounds,
    filter_dataframe_by_altitude,
    clean_dataframe_nulls,
    extract_adsb_columns,
    identify_landing_runway, identify_landing_runway_backwards
)
from tools_import import load_parquet_files


def process_adsb_data_1day(year, month, day, delta_days=0, output_dir="output", base_path="data/engage-hackathon-2025", model: str="fap"):
    """
    Process ADS-B data for a given date or date range.

    Parameters:
        year, month, day: int
            Start date components.
        delta_days: int
            Number of days to add to the start date. If zero, a single day is processed.
        output_dir: str
            Directory where the output files will be saved.
        base_path: str
            Base path for the input parquet files.
    """
    # Compute start and end dates
    start_date = date(year, month, day)
    end_date = start_date + timedelta(days=delta_days) if delta_days > 0 else start_date

    # Build output prefix based on date or date range
    if start_date == end_date:
        output_prefix = os.path.join(output_dir, f"save_{start_date.strftime('%Y_%m_%d')}")
    else:
        output_prefix = os.path.join(output_dir, f"save_{start_date.strftime('%Y_%m_%d')}_to_{end_date.strftime('%Y_%m_%d')}")

    # Define cache file names using the output prefix
    cache_file = f"{output_prefix}_cached_df.pkl"
    cache_file2 = f"{output_prefix}_cached2_df.pkl"
    cache_file3 = f"{output_prefix}_cached_landing.pkl"

    # --- Load Dataframe with Caching ---
    if os.path.exists(cache_file):
        print(f"Loading cached dataframe from {cache_file} ...")
        df = pd.read_pickle(cache_file)
    else:
        print("Cache file not found. Processing data ...")
        df = load_parquet_files(
            start_date.year, start_date.month, start_date.day, 0,
            end_date.year, end_date.month, end_date.day, 23,
            base_path=base_path
        )
        if df.empty:
            print(f"No data found for the specified period: {output_prefix}")
            return
        print(f"Saving processed dataframe to cache file {cache_file} ...")
        df.to_pickle(cache_file)

    # --- Clean and Process Dataframe with Caching ---
    if os.path.exists(cache_file2):
        print(f"Loading cached dataframe2 from {cache_file2} ...")
        df = pd.read_pickle(cache_file2)
    else:
        print("Cache file2 not found. Processing data ...")
        print("Cleaning dataframe nulls ...")
        columns_to_clean = ['altitude', 'lat_deg', 'lon_deg']
        df_filtered = clean_dataframe_nulls(df, columns_to_clean)

        print("Extracting ADS-B columns ...")
        columns_to_extract = None  # or specify a list if needed
        df_extracted = extract_adsb_columns(df_filtered, columns_to_extract)

        print("Sorting dataframe ...")
        sorted_df = sort_dataframe(df_extracted)

        print("Identifying segments ...")
        df_segments, df_extra = identify_segments(sorted_df)

        # Final dataframe for further processing
        df = df_segments

        print("Filtering dataframe by geographical bounds ...")
        min_lat, max_lat, min_lon, max_lon = [40.3, 40.8, -3.8, -3.3]  # [deg]
        df = filter_dataframe_by_bounds(df, min_lat, max_lat, min_lon, max_lon)

        print("Filtering dataframe by altitude ...")
        min_alt, max_alt = [-1000, 10000]  # [ft]
        df = filter_dataframe_by_altitude(df, min_alt, max_alt)

        print(f"Saving processed dataframe to cache file2 {cache_file2} ...")
        df.to_pickle(cache_file2)

    # --- Identify Landing Runways with Caching ---
    if os.path.exists(cache_file3):
        print(f"Loading cached landing runway results from {cache_file3} ...")
        df_with_runway, basic_info_df, df_segments_ils = pd.read_pickle(cache_file3)
    else:
        print("Cache file for landing runway not found. Processing landing runway results ...")
        if model == "fap":
            df_with_runway, basic_info_df, df_segments_ils = identify_landing_runway(df)
        elif model == "backwards":
            df_with_runway, basic_info_df, df_segments_ils = identify_landing_runway_backwards(df)
        else:
            print("Model not recognized.")

        print(f"Saving landing runway results to cache file {cache_file3} ...")
        pd.to_pickle((df_with_runway, basic_info_df, df_segments_ils), cache_file3)

    # --- Analysis and Plotting ---
    # Define time thresholds (in seconds)
    min_delta = 100
    max_delta = 500

    print(basic_info_df)

    normal_basic_info_df = basic_info_df[
        (basic_info_df['delta_time_fap_to_thr'] >= min_delta) &
        (basic_info_df['delta_time_fap_to_thr'] <= max_delta)
    ]

    stats = compute_delta_time_statistics(normal_basic_info_df, output_prefix=output_prefix)

    # Compute and print statistics by runway
    stats_by_runway = {}
    for runway, runway_df in normal_basic_info_df.groupby('runway_fap'):
        stats_by_runway[runway] = compute_delta_time_statistics(runway_df)
        print(f"Statistics for Runway {runway}:")
        for stat_name, value in stats_by_runway[runway].items():
            print(f"  {stat_name}: {value}")
        print()

    # PDF plots global
    normal_df_segments_ils = df_segments_ils[
        (df_segments_ils['delta_time_fap_to_thr'] >= min_delta) &
        (df_segments_ils['delta_time_fap_to_thr'] <= max_delta)
    ]
    df_times = compute_segment_delta_times(normal_df_segments_ils)
    plot_delta_time_pdf(df_times, output_prefix=output_prefix)

    # PDF plots per runway
    plot_delta_time_pdf_by_runway(normal_basic_info_df, output_prefix=output_prefix)

    # --- Training subset ---

    df_training_subset = normal_basic_info_df[
        ['icao24', 'runway_fap', 'ts_fap', 'ts_thr',
         'distance_fap_to_thr', 'delta_time_fap_to_thr',
         'speed_fap', 'vertical_speed_fap', 'heading_fap']
    ].copy()  # Create a copy to avoid SettingWithCopyWarning

    # Add a new column 'weekday' computed from 'ts_fap'
    df_training_subset['weekday'] = df_training_subset['ts_fap'].apply(get_day_of_week)

    # --- Exporting Results ---

    print("Exporting training CSV ...")
    export_trajectories_to_csv(df_training_subset, output_prefix + '_training.csv')

    print("Exporting all CSV ...")
    export_trajectories_to_csv(df, output_prefix + '_all.csv')

    print("Exporting filtered CSV ...")
    export_trajectories_to_csv(normal_basic_info_df, output_prefix + '_filtered_ils.csv')

    print("Exporting all KML ...")
    export_trajectories_to_kml(df, output_prefix + '_all.kml')

    print("Exporting segments KML ...")
    export_trajectories_to_kml(df_segments_ils, output_prefix + '_segments_all.kml')
    export_trajectories_to_kml(normal_df_segments_ils, output_prefix + '_segments_all_filtered.kml')
