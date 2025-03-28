
import glob
import os
import sys
from datetime import datetime, timedelta

import pandas as pd

from tools_filter import extract_adsb_columns, filter_dataframe_by_icao, clean_dataframe_nulls


def generate_dates_list(start_year, start_month, start_day, start_hour,
                        end_year, end_month, end_day, end_hour):
    """
    Generate a list of datetime objects for each hour between the start and end date-time (inclusive).

    Args:
        start_year (int): Start year.
        start_month (int): Start month.
        start_day (int): Start day.
        start_hour (int): Start hour (0-23).
        end_year (int): End year.
        end_month (int): End month.
        end_day (int): End day.
        end_hour (int): End hour (0-23).

    Returns:
        list: A list of datetime objects for each hour between the start and end.
    """
    start_dt = datetime(start_year, start_month, start_day, start_hour)
    end_dt = datetime(end_year, end_month, end_day, end_hour)
    dates = []
    current = start_dt
    while current <= end_dt:
        dates.append(current)
        current += timedelta(hours=1)
    return dates


def generate_folder_paths(dates_list, base_path):
    """
    Generate a list of folder paths for the given list of datetime objects,
    according to the folder structure: data/year=YYYY/month=MM/day=DD/hour=H.

    Args:
        dates_list (list): A list of datetime objects.
        base_path (str): The base directory containing the data. Default is "data".

    Returns:
        list: A list of folder paths as strings.
    """
    folder_paths = []
    for dt in dates_list:
        folder_path = os.path.join(
            base_path,
            f"year={dt.year}",
            f"month={dt.month}",
            f"day={dt.day}",
            f"hour={dt.hour}"
        )
        folder_paths.append(folder_path)
    return folder_paths


def load_adsb_data(input_file: str) -> pd.DataFrame:
    """
    Load raw ADS-B data from a parquet file.

    Args:
        input_file (str): The path to the input parquet file.

    Returns:
        pd.DataFrame: The raw data loaded from the file.
    """
    try:
        df = pd.read_parquet(input_file)
    except Exception as e:
        print(f"Error reading the parquet file {input_file}: {e}")
        sys.exit(1)
    print(f"Loaded {len(df)} rows from {input_file}")
    return df


def load_parquet_files(start_year, start_month, start_day, start_hour,
                       end_year, end_month, end_day, end_hour, base_path):
    """
    Load all parquet files from the folders corresponding to each hour between the start and end date-time.

    Args:
        start_year, start_month, start_day, start_hour: Start date-time components.
        end_year, end_month, end_day, end_hour: End date-time components.
        base_path (str): The base directory containing the data folders.

    Returns:
        pd.DataFrame: A combined DataFrame containing data from all parquet files in the specified range.
    """
    dates_list = generate_dates_list(start_year, start_month, start_day, start_hour,
                                     end_year, end_month, end_day, end_hour)
    folder_paths = generate_folder_paths(dates_list, base_path)

    df_list = []
    for folder in folder_paths:
        # Match all parquet files in the folder (e.g., "*.snappy.parquet" if needed)
        pattern = os.path.join(folder, "*.parquet")
        files = glob.glob(pattern)
        df = load_and_process_parquet_files(files, columns_to_extract=['df', 'icao24', 'ts', 'altitude', 'lat_deg', 'lon_deg'])
        df_list.append(df)

    # Ensure that df_list is an iterable of DataFrames.
    combined_df = pd.concat(df_list, ignore_index=True)

    # Return combined dataframe
    return combined_df


def load_and_process_parquet_files(file_list: list, icao24_list: list = None,
                                   columns_to_clean: list = None, columns_to_extract: list = None) -> pd.DataFrame:
    """
    Incrementally load, filter, and extract columns from a list of parquet files.
    This approach reduces memory usage by processing each file individually.

    Args:
        file_list (list): List of parquet file paths.
        icao24_list (list, optional): List of aircraft identifiers to filter by. Defaults to None.
        columns_to_clean (list, optional): List of columns to clean. All rows with null are removed.
            Defaults to ['lat_deg', 'lon_deg', 'altitude', 'ts']
        columns_to_extract (list, optional): List of columns to extract.
            Defaults to ['icao24', 'altitude', 'lat_deg', 'lon_deg', 'ts'].

    Returns:
        pd.DataFrame: The combined DataFrame after processing all files.
    """
    df_list = []
    for file in file_list:
        # Load raw data from the file.
        df_raw = load_adsb_data(file)
        # Filter the data based on provided icao24 identifiers and non-null altitude/lat_deg.
        df_filtered = filter_dataframe_by_icao(df_raw, icao24_list)
        # Filter the data to remove null altitude/lat_deg.
        df_filtered = clean_dataframe_nulls(df_filtered, columns_to_clean)
        # Extract the required subset of columns.
        df_extracted = extract_adsb_columns(df_filtered, columns_to_extract)
        df_list.append(df_extracted)
    if df_list:
        combined_df = pd.concat(df_list, ignore_index=True)
    else:
        combined_df = pd.DataFrame()
    return combined_df
