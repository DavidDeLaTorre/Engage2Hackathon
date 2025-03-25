#!/usr/bin/env python3
"""
This script processes ADS-B data stored in a parquet file, for 1 day
"""
import os
from datetime import date, timedelta

from tools_import import generate_dates_list
from tools_process import process_adsb_data_1day


def main():

    # Output directory
    output_dir = 'output/training_data'
    os.makedirs(output_dir, exist_ok=True)

    # Date ranges
    start_year, start_month, start_day = [2024,11,16]
    end_year, end_month, end_day = [2024,11,30]

    # Create date objects for start and end dates
    start_date = date(start_year, start_month, start_day)
    end_date = date(end_year, end_month, end_day)

    # Generate list of dates from start_date to end_date inclusive
    dates_list = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    # Process all dates
    for dt in dates_list:
        process_adsb_data_1day(dt.year, dt.month, dt.day, output_dir=output_dir)


if __name__ == '__main__':
    main()
