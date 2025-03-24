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
from tools_export import export_trajectories_to_csv, export_trajectories_to_kml, \
    export_trajectories_FAP_predicted_FAP_to_kml
from math import radians, sin, cos, sqrt, atan2
from tools_filter import find_nearest_point

from FAP_positions import FAP_position
from threshold_positions import threshold_position

def main():
    # Ensure that the correct number of arguments are provided.
    if len(sys.argv) != 4:
        input_file = "data/engage-hackathon-2025/year=2024/month=11/day=16/hour=12/1225667186084f958614500e99a47e92.snappy.parquet"
        icao24 = "01024c"
        output_csv = "output/icao24_"+icao24+".csv"
        output_kml = "output/icao24_"+icao24+".kml"
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

    result = find_nearest_point(baseline_position=FAP_position, filtered_df=filtered_df)
    print(f"Nearest point is at index {result['index']} near runway {result['runway']}")
    print(result['point'])

    # ########
    # index = filtered_df.loc[result['index']]
    # FAP_record = filtered_df[index]
    # print("FAP_record")
    # print(FAP_record)

    # Export the trajectory to a KML file.
    export_trajectories_FAP_predicted_FAP_to_kml(df=filtered_df, output_file=output_kml, FAP_position=FAP_position, nearest_fap_info=result)

if __name__ == '__main__':
    main()
