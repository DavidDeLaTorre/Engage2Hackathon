import datetime
import math
from typing import List, Optional

import numpy as np
import pandas as pd

from math import radians, sin, cos, sqrt, atan2, asin

from FAP_positions import FAP_position
from threshold_positions import threshold_position


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
    Identify separate trajectory segments in ADS-B data based on time gaps and classify each segment,
    processing the data for each unique flight (icao24) individually.

    Parameters:
      df (pd.DataFrame): DataFrame containing ADS-B data with at least 'ts', 'altitude', and 'icao24' columns.
      time_gap_threshold (int, optional): The time gap threshold (in seconds) used to define a new segment.
                                          Defaults to 3600 seconds (1 hour).

    Returns:
      tuple:
        - annotated_df (pd.DataFrame): The original DataFrame with additional columns:
              * 'time_gap': Time difference between consecutive points.
              * 'segment': Segment identifier.
              * 'trajectory': Classification of the segment ('departing', 'landing', or 'level').
        - segment_summary (pd.DataFrame): Summary statistics for each identified segment including:
              * 'icao24': Flight identifier.
              * 'segment': Segment ID.
              * 'start_time': First timestamp in the segment.
              * 'end_time': Last timestamp in the segment.
              * 'start_altitude': Altitude at the beginning of the segment.
              * 'end_altitude': Altitude at the end of the segment.
              * 'altitude_change': Overall altitude change in the segment.
              * 'trajectory': Classification of the segment.
    """
    annotated_list = []
    segment_summary_list = []

    # Process each flight separately by grouping on 'icao24'
    for icao, group in df.groupby('icao24'):
        # Ensure the data is sorted by timestamp
        group = group.sort_values('ts').copy()

        # Compute time difference between consecutive rows (converted to seconds)
        group['time_gap'] = group['ts'].diff().fillna(0) / 1000

        # Create a new segment whenever the time gap exceeds the threshold.
        # Each flight has its own segment numbering.
        group['segment'] = (group['time_gap'] > time_gap_threshold).cumsum()

        # Compute summary statistics for each segment in the flight.
        seg_summary = group.groupby('segment').agg(
            start_time=('ts', 'first'),
            end_time=('ts', 'last'),
            start_altitude=('altitude', 'first'),
            end_altitude=('altitude', 'last')
        ).reset_index()

        # Calculate overall altitude change for each segment.
        seg_summary['altitude_change'] = seg_summary['end_altitude'] - seg_summary['start_altitude']

        # Classify each segment.
        seg_summary['trajectory'] = np.where(
            seg_summary['altitude_change'] > 0, 'departing',
            np.where(seg_summary['altitude_change'] < 0, 'landing', 'level')
        )

        # Add the flight identifier to the segment summary.
        seg_summary['icao24'] = icao

        # Merge the trajectory classification back into the group's DataFrame.
        group = group.merge(seg_summary[['segment', 'trajectory']], on='segment', how='left')

        # (Optionally) Reinforce the flight identifier in the group's DataFrame.
        group['icao24'] = icao

        # Append the results for this flight.
        annotated_list.append(group)
        segment_summary_list.append(seg_summary)

    # Combine the annotated data and summaries from all flights.
    annotated_df = pd.concat(annotated_list).reset_index(drop=True)
    segment_summary = pd.concat(segment_summary_list).reset_index(drop=True)

    return annotated_df, segment_summary


def haversine(lat1, lon1, lat2, lon2):
    # Radius of Earth in meters
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)

    a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Calculate the bearing between two points.
    All args must be in decimal degrees.
    """
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1

    x = np.sin(dlon) * np.cos(lat2)
    y = np.cos(lat1)*np.sin(lat2) - np.sin(lat1)*np.cos(lat2)*np.cos(dlon)

    initial_bearing = np.arctan2(x, y)
    initial_bearing = np.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

def find_last_no_turning_point(group_df, nearest_thr):
    runway = nearest_thr['runway']
    index = nearest_thr['index']
    runway_heading = float(runway[:2])*10
    offset = 10

    group_df['bearing'] = group_df.apply(lambda row: calculate_bearing(row['lat_deg'], row['lon_deg'], nearest_thr["point"]["lat_deg"], nearest_thr["point"]["lon_deg"]), axis=1)

    nearest = {
        'distance': float('inf'),
        'runway': None,
        'point': None,
        'index': None
    }

    group_df['within_range'] = (group_df['bearing'] >= runway_heading - offset) & (group_df['bearing'] <= runway_heading + offset)

    if not group_df['within_range'].unique()[0]:
        return None

    last_true_row = group_df[group_df['within_range']].iloc[-1]
    last_true_index = group_df[group_df['within_range']].index[-1]

    nearest['distance'] = 0
    nearest['runway'] = runway
    nearest['point'] = last_true_row
    nearest['index'] = last_true_index
    # Save the timestamp from the 'ts' field of the corresponding row
    nearest['ts'] = last_true_row['ts']

    return nearest

def find_nearest_point(baseline_position: dict, filtered_df: pd.DataFrame):
    # Make sure filtered_df has numeric lat/lon
    df = filtered_df.copy()
    df = df.dropna(subset=['lat_deg', 'lon_deg'])

    nearest = {
        'distance': float('inf'),
        'runway': None,
        'point': None,
        'base_lat': None,
        'base_lon': None,
        'index': None,
        'ts': None
    }

    for runway, point in baseline_position.items():
        # Compute haversine distance from all points to this FAP
        distances = df.apply(
            lambda row: haversine(row['lat_deg'], row['lon_deg'], point.latitude, point.longitude),
            axis=1
        )

        min_idx = distances.idxmin()
        min_distance = distances[min_idx]

        if min_distance < nearest['distance']:
            nearest['distance'] = min_distance
            nearest['runway'] = runway
            nearest['point'] = df.loc[min_idx]
            nearest['base_lat'] = point.latitude
            nearest['base_lon'] = point.longitude
            nearest['index'] = min_idx
            nearest['ts'] = df.loc[min_idx]['ts']

    return nearest


def compute_bearing(lat1, lon1, lat2, lon2):
    # Convert latitude/longitude from degrees to radians.
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)
    x = math.sin(delta_lon) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lon)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def identify_landing_runway(df):
    results = []
    basic_info_results = []
    segments_ils_results = []  # List to collect the trajectory segments (ILS segments)

    # Filter out unwanted trajectories
    if 'trajectory' in df.columns:
        df = df[~df['trajectory'].isin(['departing', 'level'])]

    # Group by icao24 and segment
    grouped = df.groupby(['icao24', 'segment'])

    for (icao24, segment), group_df in grouped:

        # Get a representative timestamp from the group (using the first row)
        rep_ts = group_df['ts'].iloc[0]
        rep_date = datetime.datetime.utcfromtimestamp(rep_ts / 1000).strftime('%Y-%m-%d %Hh')

        # Find the nearest point to the FAP position and to the threshold position.
        nearest_fap = find_nearest_point(FAP_position, group_df)
        nearest_thr = find_nearest_point(threshold_position, group_df)

        # Ensure that the runways are the same
        if nearest_fap['runway'] != nearest_thr['runway']:
            print(f'  icao24 {icao24} at ts {rep_ts} ({rep_date}): runways do not match: '
                  f'{nearest_fap["runway"]} != {nearest_thr["runway"]}')
            continue

        # Ensure that the found points are "close enough" to the FAP
        if nearest_fap['distance'] > 700:  # [meters]
            print(f'  icao24 {icao24} at ts {rep_ts} ({rep_date}): FAP distance too large: {nearest_fap["distance"]}')
            continue

        # Ensure that the found points are "close enough" to the THR
        if nearest_thr['distance'] > 700:  # [meters]
            print(f'  icao24 {icao24} at ts {rep_ts} ({rep_date}): THR distance too large: {nearest_thr["distance"]}')
            continue

        # Augment the group's dataframe with runway and index/timestamp info
        group_df = group_df.copy()
        group_df['runway_fap'] = nearest_fap['runway']
        group_df['runway_thr'] = nearest_thr['runway']
        group_df['idx_fap'] = nearest_fap['index']
        group_df['idx_thr'] = nearest_thr['index']
        group_df['ts_fap'] = nearest_fap['ts']
        group_df['ts_thr'] = nearest_thr['ts']

        # Compute and add delta_time to each row in the group
        delta_time_real = (nearest_thr['ts'] - nearest_fap['ts']) / 1000
        group_df['delta_time'] = delta_time_real

        # Extract coordinates for the nearest FAP and threshold points
        lat_fap = group_df.loc[nearest_fap['index'], 'lat_deg']
        lon_fap = group_df.loc[nearest_fap['index'], 'lon_deg']
        lat_thr = group_df.loc[nearest_thr['index'], 'lat_deg']
        lon_thr = group_df.loc[nearest_thr['index'], 'lon_deg']

        # Compute the distance between the nearest FAP point and the nearest threshold point
        distance_real = haversine(lat_fap, lon_fap, lat_thr, lon_thr)

        # Compute the "true" distance between the actual FAP and THR positions
        true_distance = haversine(nearest_fap["base_lat"], nearest_fap["base_lon"],
                                  nearest_thr["base_lat"], nearest_thr["base_lon"])

        # Compute a scaling factor (avoid division by zero)
        scaling_factor = true_distance / distance_real if distance_real != 0 else 1

        # Re-scale the delta_time and distance
        delta_time_scaled = delta_time_real * scaling_factor
        distance_scaled = distance_real * scaling_factor  # This should be equal to true_distance

        # Save the scaled values to the group dataframe
        group_df['distance_fap_to_thr'] = true_distance
        group_df['delta_time_fap_to_thr'] = delta_time_scaled

        # ----- New Computations at the FAP Point -----
        # Compute speed, vertical_speed, and heading at the FAP point using the previous data point.
        # We sort by timestamp to ensure the points are in chronological order.
        group_df_sorted = group_df.sort_values('ts')
        try:
            # Get the position of the FAP point in the sorted dataframe
            fap_pos = group_df_sorted.index.get_loc(nearest_fap['index'])
        except Exception as e:
            fap_pos = None

        if fap_pos is not None and fap_pos > 0:
            previous_point = group_df_sorted.iloc[fap_pos - 1]
            # Time difference in seconds
            dt = (nearest_fap['ts'] - previous_point['ts']) / 1000.0
            if dt > 0:
                # Compute horizontal distance in meters between previous point and FAP point.
                horiz_distance = haversine(lat_fap, lon_fap, previous_point['lat_deg'], previous_point['lon_deg'])
                speed = horiz_distance / dt  # in m/s
                # Compute vertical speed using altitude difference (assumes 'altitude' column exists)
                vertical_speed = (group_df.loc[nearest_fap['index'], 'altitude'] - previous_point['altitude']) / dt
                # Compute heading (bearing) from the previous point to the FAP point.
                heading = compute_bearing(previous_point['lat_deg'], previous_point['lon_deg'], lat_fap, lon_fap)
            else:
                speed, vertical_speed, heading = None, None, None
        else:
            speed, vertical_speed, heading = None, None, None

        # Build the basic info dictionary for this icao24 segment including the new fields.
        basic_info = {
            'icao24': icao24,
            'runway_fap': nearest_fap['runway'],
            'idx_fap': nearest_fap['index'],
            'idx_thr': nearest_thr['index'],
            'ts_fap': nearest_fap['ts'],
            'ts_thr': nearest_thr['ts'],
            'lat_deg_fap': lat_fap,
            'lon_deg_fap': lon_fap,
            'lat_deg_thr': lat_thr,
            'lon_deg_thr': lon_thr,
            'distance': distance_real,
            'delta_time': delta_time_real,
            'distance_fap_to_thr': true_distance,
            'delta_time_fap_to_thr': delta_time_scaled,
            'speed_fap': speed,
            'vertical_speed_fap': vertical_speed,
            'heading_fap': heading
        }
        basic_info_results.append(basic_info)
        # ---------------------------------------------

        # Extract the ILS segment: the rows between the FAP and THR identified points.
        try:
            pos_fap = group_df.index.get_loc(nearest_fap['index'])
            pos_thr = group_df.index.get_loc(nearest_thr['index'])
        except Exception as e:
            print(f"Error determining positions for icao24 {icao24}: {e}")
            continue

        start_pos = min(pos_fap, pos_thr)
        end_pos = max(pos_fap, pos_thr) + 1  # +1 to include the endpoint
        segment_ils = group_df.iloc[start_pos:end_pos]
        segments_ils_results.append(segment_ils)

        # Add group to the results
        results.append(group_df)

    # Concatenate the augmented group dataframes
    df_with_runway = pd.concat(results).reset_index(drop=True)

    # Create the smaller dataframe with basic info for each icao24 segment
    basic_info_df = pd.DataFrame(basic_info_results)

    # Concatenate the ILS segments (if any) into a single dataframe
    df_segments_ils = pd.concat(segments_ils_results).reset_index(drop=True) if segments_ils_results else pd.DataFrame()

    return df_with_runway, basic_info_df, df_segments_ils

def identify_landing_runway_backwards(df):
    results = []
    basic_info_results = []
    segments_ils_results = []  # List to collect the trajectory segments (ILS segments)

    # Filter out unwanted trajectories
    df = df[~df['trajectory'].isin(['departing', 'level'])]

    # Group by icao24 and segment
    grouped = df.groupby(['icao24', 'segment'])

    for (icao24, segment), group_df in grouped:

        # Get a representative timestamp from the group (using the first row)
        rep_ts = group_df['ts'].iloc[0]
        rep_date = datetime.datetime.utcfromtimestamp(rep_ts / 1000).strftime('%Y-%m-%d %Hh')


        # Find the nearest point to the FAP position and to the threshold position.
        nearest_thr = find_nearest_point(threshold_position, group_df)
        nearest_fap = find_last_no_turning_point(group_df, nearest_thr)

        if nearest_fap is None:
            print(f'  icao24 {icao24} at ts {rep_ts} ({rep_date}): heading do not match')
            continue # Nos el follem perque no esta prop del bearing esperat

        # Ensure that the runways are the same
        if nearest_fap['runway'] != nearest_thr['runway']:
            print(f'  icao24 {icao24} at ts {rep_ts} ({rep_date}): runways do not match: '
                  f'{nearest_fap["runway"]} != {nearest_thr["runway"]}')
            continue

        # Ensure that the found points are "close enough" to the FAP
        if nearest_fap['distance'] > 700:  # [meters]
            print(f'  icao24 {icao24} at ts {rep_ts} ({rep_date}): FAP distance too large: {nearest_fap["distance"]}')
            continue

        # Ensure that the found points are "close enough" to the THR
        if nearest_thr['distance'] > 700:  # [meters]
            print(f'  icao24 {icao24} at ts {rep_ts} ({rep_date}): THR distance too large: {nearest_thr["distance"]}')
            continue

        # Augment the group's dataframe with runway and index/timestamp info
        group_df = group_df.copy()
        group_df['runway_fap'] = nearest_fap['runway']
        group_df['runway_thr'] = nearest_thr['runway']
        group_df['idx_fap'] = nearest_fap['index']
        group_df['idx_thr'] = nearest_thr['index']
        group_df['ts_fap'] = nearest_fap['ts']
        group_df['ts_thr'] = nearest_thr['ts']

        # Compute and add delta_time to each row in the group
        delta_time = (nearest_thr['ts'] - nearest_fap['ts']) / 1000
        group_df['delta_time'] = delta_time

        results.append(group_df)

        # Extract coordinates for the nearest FAP and threshold df points
        lat_fap = group_df.loc[nearest_fap['index'], 'lat_deg']
        lon_fap = group_df.loc[nearest_fap['index'], 'lon_deg']
        lat_thr = group_df.loc[nearest_thr['index'], 'lat_deg']
        lon_thr = group_df.loc[nearest_thr['index'], 'lon_deg']

        # Compute the distance between the nearest FAP point and the nearest threshold point
        distance = haversine(lat_fap, lon_fap, lat_thr, lon_thr)

        # Build the basic info dictionary for this icao24 segment
        basic_info = {
            'icao24': icao24,
            'runway_fap': nearest_fap['runway'],
            'idx_fap': nearest_fap['index'],
            'idx_thr': nearest_thr['index'],
            'ts_fap': nearest_fap['ts'],
            'ts_thr': nearest_thr['ts'],
            'delta_time': delta_time,
            'lat_deg_fap': lat_fap,
            'lon_deg_fap': lon_fap,
            'lat_deg_thr': lat_thr,
            'lon_deg_thr': lon_thr,
            'distance_fap_to_thr': distance
        }
        basic_info_results.append(basic_info)

        # Extract the ILS segment: the rows between the FAP and THR identified points.
        # We first get their positional indexes in the group's dataframe.
        try:
            pos_fap = group_df.index.get_loc(nearest_fap['index'])
            pos_thr = group_df.index.get_loc(nearest_thr['index'])
        except Exception as e:
            print(f"Error determining positions for icao24 {icao24}: {e}")
            continue

        start_pos = min(pos_fap, pos_thr)
        end_pos = max(pos_fap, pos_thr) + 1  # +1 to include the endpoint
        segment_ils = group_df.iloc[start_pos:end_pos]
        segments_ils_results.append(segment_ils)

    # Concatenate the augmented group dataframes
    df_with_runway = pd.concat(results).reset_index(drop=True)

    # Create the smaller dataframe with basic info for each icao24 segment
    basic_info_df = pd.DataFrame(basic_info_results)

    # Concatenate the ILS segments (if any) into a single dataframe
    df_segments_ils = pd.concat(segments_ils_results).reset_index(drop=True) if segments_ils_results else pd.DataFrame()

    return df_with_runway, basic_info_df, df_segments_ils


def identify_landing_runway_scenario(df):
    results = []
    basic_info_results = []
    segments_ils_results = []  # List to collect the trajectory segments (ILS segments)

    # Filter out unwanted trajectories
    if 'trajectory' in df.columns:
        df = df[~df['trajectory'].isin(['departing', 'level'])]

    # Group by icao24 and segment
    grouped = df.groupby(['icao24', 'segment'])

    for (icao24, segment), group_df in grouped:

        # Get a representative timestamp from the group (using the first row)
        rep_ts = group_df['ts'].iloc[0]
        rep_date = datetime.datetime.utcfromtimestamp(rep_ts / 1000).strftime('%Y-%m-%d %Hh')

        # Find the nearest point to the FAP position and to the threshold position.
        nearest_fap = find_nearest_point(FAP_position, group_df)
        nearest_thr = find_nearest_point(threshold_position, group_df)

        # Augment the group's dataframe with runway and index/timestamp info
        group_df = group_df.copy()
        group_df['runway_fap'] = nearest_fap['runway']
        group_df['runway_thr'] = nearest_thr['runway']
        group_df['idx_fap'] = nearest_fap['index']
        group_df['idx_thr'] = nearest_thr['index']
        group_df['ts_fap'] = nearest_fap['ts']
        group_df['ts_thr'] = nearest_thr['ts']

        # Compute and add delta_time to each row in the group
        delta_time_real = (nearest_thr['ts'] - nearest_fap['ts']) / 1000
        group_df['delta_time'] = delta_time_real

        # Extract coordinates for the nearest FAP and threshold df points
        lat_fap = group_df.loc[nearest_fap['index'], 'lat_deg']
        lon_fap = group_df.loc[nearest_fap['index'], 'lon_deg']
        lat_thr = group_df.loc[nearest_thr['index'], 'lat_deg']
        lon_thr = group_df.loc[nearest_thr['index'], 'lon_deg']

        # Compute the distance between the nearest FAP point and the nearest threshold point
        distance_real = haversine(lat_fap, lon_fap, lat_thr, lon_thr)

        # Compute the "true" distance between the actual FAP and THR positions
        true_distance = haversine(nearest_fap["base_lat"], nearest_fap["base_lon"],
                                  nearest_thr["base_lat"], nearest_thr["base_lon"])

        # Compute a scaling factor (avoid division by zero)
        scaling_factor = true_distance / distance_real if distance_real != 0 else 1

        # Re-scale the delta_time and distance
        delta_time_scaled = delta_time_real * scaling_factor
        distance_scaled = distance_real * scaling_factor  # This should be equal to true_distance

        # --- New Computations for the Scenario Pair ---
        # Compute the distance between the real FAP point and the true threshold (using base coordinates)
        distance_scenario = haversine(
            lat_fap, lon_fap,
            nearest_thr["base_lat"], nearest_thr["base_lon"]
        )
        # Compute the corresponding time assuming a constant speed (scale delta_time_real proportionally)
        time_scenario = delta_time_real * (distance_scenario / distance_real) if distance_real != 0 else delta_time_real

        # Save the scaled values to the group dataframe
        group_df['distance_fap_to_thr'] = true_distance
        group_df['delta_time_fap_to_thr'] = delta_time_scaled

        # ----- New Computations at the FAP Point -----
        # Compute speed, vertical_speed, and heading at the FAP point using the previous data point.
        # We sort by timestamp to ensure the points are in chronological order.
        group_df_sorted = group_df.sort_values('ts')
        try:
            # Get the position of the FAP point in the sorted dataframe
            fap_pos = group_df_sorted.index.get_loc(nearest_fap['index'])
        except Exception as e:
            fap_pos = None

        if fap_pos is not None and fap_pos > 0:
            previous_point = group_df_sorted.iloc[fap_pos - 1]
            # Time difference in seconds
            dt = (nearest_fap['ts'] - previous_point['ts']) / 1000.0
            if dt > 0:
                # Compute horizontal distance in meters between previous point and FAP point.
                horiz_distance = haversine(lat_fap, lon_fap, previous_point['lat_deg'], previous_point['lon_deg'])
                speed = horiz_distance / dt  # in m/s
                # Compute vertical speed using altitude difference (assumes 'altitude' column exists)
                vertical_speed = (group_df.loc[nearest_fap['index'], 'altitude'] - previous_point['altitude']) / dt
                # Compute heading (bearing) from the previous point to the FAP point.
                heading = compute_bearing(previous_point['lat_deg'], previous_point['lon_deg'], lat_fap, lon_fap)
            else:
                speed, vertical_speed, heading = None, None, None
        else:
            speed, vertical_speed, heading = None, None, None

        # Build the basic info dictionary for this icao24 segment including the new fields.
        basic_info = {
            'icao24': icao24,
            'runway_fap': nearest_fap['runway'],
            'idx_fap': nearest_fap['index'],
            'idx_thr': nearest_thr['index'],
            'ts_fap': nearest_fap['ts'],
            'ts_thr': nearest_thr['ts'],
            'lat_deg_fap': lat_fap,
            'lon_deg_fap': lon_fap,
            'lat_deg_thr': lat_thr,
            'lon_deg_thr': lon_thr,
            'distance': distance_real,
            'delta_time': delta_time_real,
            'distance_fap_to_thr': true_distance,
            'delta_time_fap_to_thr': delta_time_scaled,
            'speed_fap': speed,
            'vertical_speed_fap': vertical_speed,
            'heading_fap': heading,
            'distance_scenario': distance_scenario,
            'time_scenario': time_scenario
        }
        basic_info_results.append(basic_info)
        # ---------------------------------------------

        # Extract the ILS segment: the rows between the FAP and THR identified points.
        # We first get their positional indexes in the group's dataframe.
        try:
            pos_fap = group_df.index.get_loc(nearest_fap['index'])
            pos_thr = group_df.index.get_loc(nearest_thr['index'])
        except Exception as e:
            print(f"Error determining positions for icao24 {icao24}: {e}")
            continue

        start_pos = min(pos_fap, pos_thr)
        end_pos = max(pos_fap, pos_thr) + 1  # +1 to include the endpoint
        segment_ils = group_df.iloc[start_pos:end_pos]
        segments_ils_results.append(segment_ils)

        # Add group to the results
        results.append(group_df)

    # Concatenate the augmented group dataframes
    df_with_runway = pd.concat(results).reset_index(drop=True)

    # Create the smaller dataframe with basic info for each icao24 segment
    basic_info_df = pd.DataFrame(basic_info_results)

    # Concatenate the ILS segments (if any) into a single dataframe
    df_segments_ils = pd.concat(segments_ils_results).reset_index(drop=True) if segments_ils_results else pd.DataFrame()

    return df_with_runway, basic_info_df, df_segments_ils
