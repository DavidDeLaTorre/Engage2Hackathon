from typing import List, Optional

import numpy as np
import pandas as pd


def sort_dataframe(df: pd.DataFrame, fields: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Sorts a DataFrame based on a given list of fields.

    If no list of fields is provided, the DataFrame is automatically sorted
    by the default fields: 'icao24' and then 'ts' (time).

    Parameters:
        df (pd.DataFrame): The input DataFrame to be sorted.
        fields (Optional[List[str]]): A list of column names to sort by.
                                      Defaults to None, which triggers auto-sorting
                                      by ['icao24', 'ts'].

    Returns:
        pd.DataFrame: A new DataFrame sorted by the specified fields.

    Raises:
        KeyError: If any of the specified sorting fields are not in the DataFrame.
    """
    # If no sorting fields are provided, use default fields
    if fields is None:
        fields = ['icao24', 'ts']

    # Ensure all provided fields exist in the DataFrame columns
    missing_fields = [field for field in fields if field not in df.columns]
    if missing_fields:
        raise KeyError(f"The following fields are not in the DataFrame: {missing_fields}")

    # Return a new DataFrame sorted by the specified fields in ascending order
    sorted_df = df.sort_values(by=fields, ascending=True).reset_index(drop=True)
    return sorted_df


def extract_adsb_columns(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    """
    Extract a subset of columns from the ADS-B data.

    Args:
        df (pd.DataFrame): The ADS-B data.
        columns (list, optional): List of columns to extract.
            Defaults to ['icao24', 'altitude', 'lat_deg', 'lon_deg', 'ts'].

    Returns:
        pd.DataFrame: A DataFrame containing only the specified columns.
    """
    if columns is None:
        columns = ['icao24', 'altitude', 'lat_deg', 'lon_deg', 'ts']
    missing_cols = [col for col in columns if col not in df.columns]
    if missing_cols:
        print(f"Warning: The following columns are missing in the data: {missing_cols}")
    cols_to_keep = [col for col in columns if col in df.columns]
    extracted_df = df[cols_to_keep].copy()
    return extracted_df


def clean_dataframe_nulls(df: pd.DataFrame, fields: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Filter the ADS-B data to remove rows with missing altitude or latitude.

    Args:
        df (pd.DataFrame): The raw ADS-B data.
        fields (list, optional): List of fields to remove nulls from.
            If None, ['lat_deg', 'lon_deg', 'altitude', 'ts'] are processed.

    Returns:
        pd.DataFrame: The filtered DataFrame.
    """

    # Default fields to clean-up
    if fields is None:
        fields = ['lat_deg', 'lon_deg', 'altitude', 'ts']

    # Clean-up rows with null fields
    for field in fields:
        df = df[df[field].notna()]
        print(f"Rows after filtering by provided icao24 values {fields}: {len(df)}")

    return df


def filter_dataframe_by_icao(df: pd.DataFrame, icao24_list: list = None) -> pd.DataFrame:
    """
    Filter the ADS-B data by a list of icao24 identifiers.

    Args:
        df (pd.DataFrame): The raw ADS-B data.
        icao24_list (list, optional): List of aircraft identifiers to keep.
            If None, all flights are processed.

    Returns:
        pd.DataFrame: The filtered DataFrame.
    """
    if icao24_list:
        df = df[df['icao24'].isin(icao24_list)]
        print(f"Rows after filtering by provided icao24 values {icao24_list}: {len(df)}")
    else:
        print("No specific icao24 codes provided. Processing all flights.")
    return df


def filter_dataframe_by_bounds(df, min_lat, max_lat, min_lon, max_lon):
    """
    Filters the given DataFrame to only include rows where:
    - lat_deg is between min_lat and max_lat, and
    - lon_deg is between min_lon and max_lon.

    Parameters:
        df (pd.DataFrame): The input DataFrame containing 'lat_deg' and 'lon_deg' columns.
        min_lat (float): Minimum latitude.
        max_lat (float): Maximum latitude.
        min_lon (float): Minimum longitude.
        max_lon (float): Maximum longitude.

    Returns:
        pd.DataFrame: Filtered DataFrame containing only rows within the specified bounds.
    """
    filtered_df = df[
        (df['lat_deg'] >= min_lat) & (df['lat_deg'] <= max_lat) &
        (df['lon_deg'] >= min_lon) & (df['lon_deg'] <= max_lon)
    ]
    return filtered_df


def filter_dataframe_by_altitude(df, min_alt, max_alt):
    """
    Filters the given DataFrame to only include rows where:
    - altitude is between min_lat and max_lat

    Parameters:
        df (pd.DataFrame): The input DataFrame containing 'lat_deg' and 'lon_deg' columns.
        min_alt (float): Minimum altitude.
        max_alt (float): Maximum altitude.

    Returns:
        pd.DataFrame: Filtered DataFrame containing only rows within the specified bounds.
    """
    filtered_df = df[
        (df['altitude'] >= min_alt) & (df['altitude'] <= max_alt)
    ]
    return filtered_df


def identify_segments(df, time_gap_threshold=3600):
    """
    Identify separate trajectory segments in ADS-B data based on time gaps and classify each segment.

    The function processes a DataFrame containing ADS-B data, which must include at least the columns:
      - 'ts': timestamp in seconds.
      - 'altitude': altitude measurements.

    It performs the following steps:
      1. Sorts the DataFrame by timestamp.
      2. Computes the time gap between consecutive data points.
      3. Assigns a segment ID whenever the time gap exceeds the specified threshold.
      4. For each segment, calculates the overall altitude change.
      5. Classifies each segment as:
           - "departing" if the overall altitude increases.
           - "landing" if the overall altitude decreases.
           - "level" if there is negligible altitude change.
      6. Merges the segment classification back into the original DataFrame.

    Parameters:
      df (pd.DataFrame): DataFrame containing ADS-B data with at least 'ts' and 'altitude' columns.
      time_gap_threshold (int, optional): The time gap threshold (in seconds) used to define a new segment.
                                          Defaults to 3600 seconds (1 hour).

    Returns:
      tuple:
        - annotated_df (pd.DataFrame): The original DataFrame with additional columns:
              * 'time_gap': Time difference between consecutive points.
              * 'segment': Segment identifier.
              * 'trajectory': Classification of the segment ('departing', 'landing', or 'level').
        - segment_summary (pd.DataFrame): Summary statistics for each identified segment including:
              * 'segment': Segment ID.
              * 'start_time': First timestamp in the segment.
              * 'end_time': Last timestamp in the segment.
              * 'start_altitude': Altitude at the beginning of the segment.
              * 'end_altitude': Altitude at the end of the segment.
              * 'altitude_change': Overall altitude change in the segment.
              * 'trajectory': Classification of the segment.
    """

    # Compute the time difference between consecutive rows [seconds]
    df['time_gap'] = df['ts'].diff().fillna(0) / 1000

    # Create a new segment whenever the time gap exceeds the threshold.
    df['segment'] = (df['time_gap'] > time_gap_threshold).cumsum()

    # Group by each segment to compute summary statistics.
    segment_summary = df.groupby('segment').agg(
        start_time=('ts', 'first'),
        end_time=('ts', 'last'),
        start_altitude=('altitude', 'first'),
        end_altitude=('altitude', 'last')
    ).reset_index()

    # Calculate overall altitude change for each segment.
    segment_summary['altitude_change'] = segment_summary['end_altitude'] - segment_summary['start_altitude']

    # Classify each segment based on the overall altitude change.
    segment_summary['trajectory'] = np.where(
        segment_summary['altitude_change'] > 0, 'departing',
        np.where(segment_summary['altitude_change'] < 0, 'landing', 'level')
    )

    # Merge the trajectory classification back into the original DataFrame.
    annotated_df = df.merge(segment_summary[['segment', 'trajectory']], on='segment', how='left')

    return annotated_df, segment_summary
