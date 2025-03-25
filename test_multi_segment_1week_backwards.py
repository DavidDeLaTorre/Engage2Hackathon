#!/usr/bin/env python3
"""
This script processes ADS-B data stored in a parquet file, for an entire week
"""
from tools_process import process_adsb_data_1day


def main():

    # Date range
    year = 2024
    month = 11
    day = 16
    delta_days = 7

    model = "backwards"
    # Process a one-week period
    process_adsb_data_1day(year, month, day, delta_days=delta_days, model=model)


if __name__ == '__main__':
    main()
