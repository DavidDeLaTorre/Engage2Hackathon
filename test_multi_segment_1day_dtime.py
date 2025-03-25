#!/usr/bin/env python3
"""
This script processes ADS-B data stored in a parquet file, for 1 day
"""
from tools_process import process_adsb_data


def main():
    """
    Main function to process ADS-B data, filter by provided flights (if any),
    and export the results to CSV and KML files.

    Command-line arguments:
        <input_parquet_file> <output_csv_file> <output_kml_file> [icao24_1 icao24_2 ...]
    """

    # Date range
    year = 2024
    month = 11
    day = 16
    delta_days = 0

    # Process a one-day period
    process_adsb_data(year, month, day, delta_days=delta_days)


if __name__ == '__main__':
    main()
