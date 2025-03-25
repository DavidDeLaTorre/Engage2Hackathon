#!/usr/bin/env python3
"""
This script processes ADS-B data stored in a parquet file, for 1 day
"""
import os

from tools_import import generate_dates_list
from tools_process import process_adsb_data_1day


def main():

    # Output directory
    output_dir = 'output/training_data'
    os.makedirs(output_dir, exist_ok=True)

    # Date ranges
    start_year, start_month, start_day, start_hour = [2014,11,16,0]
    end_year, end_month, end_day, end_hour = [2014,11,17,23]

    dates_list = generate_dates_list(start_year, start_month, start_day, start_hour,
                                     end_year, end_month, end_day, end_hour)

    # Process all dates
    for dt in dates_list:
        process_adsb_data_1day(dt.year, dt.month, dt.day, delta_days=0, output_dir=output_dir)


if __name__ == '__main__':
    main()
