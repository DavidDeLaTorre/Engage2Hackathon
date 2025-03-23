#!/usr/bin/env python3
"""
Script to load and inspect a single Parquet file containing ADS-B aircraft trajectory data.
This script uses PyArrow to read the Parquet file, display metadata about the file (such as
schema, row groups, and column details), and prints a preview of the data as a Pandas DataFrame.

Assumptions:
- The file is one of thousands of ~25MB Parquet files.
- The contents of the file are unknown.
- Later, the approach may be extended to load an entire dataset (e.g., 30GB) efficiently.
"""

import sys
import pyarrow.parquet as pq
import pandas as pd


def load_and_inspect_parquet(filepath):
    """
    Load a Parquet file and display its metadata and a sample of the data.

    Args:
        filepath (str): Path to the Parquet file.
    """
    try:
        # Open the Parquet file for inspection
        parquet_file = pq.ParquetFile(filepath)
    except Exception as e:
        print(f"Error opening file {filepath}: {e}")
        sys.exit(1)

    # Retrieve file-level metadata
    metadata = parquet_file.metadata

    # Display basic file metadata
    print("=== File Metadata ===")
    print(f"Number of rows: {metadata.num_rows}")
    print(f"Number of row groups: {metadata.num_row_groups}")
    print(f"Created by: {metadata.created_by}")
    print("\n=== Schema ===")
    print(parquet_file.schema)  # This shows the schema including column names and types

    # Display detailed metadata for each row group
    print("\n=== Row Groups Details ===")
    for i in range(metadata.num_row_groups):
        row_group = metadata.row_group(i)
        print(f"\n-- Row Group {i} --")
        print(f"Number of rows in this group: {row_group.num_rows}")
        # Iterate over each column in the row group
        for j in range(row_group.num_columns):
            col_meta = row_group.column(j)
            # Print details about each column (path, physical type, and encodings used)
            print(f"Column {j}:")
            print(f"  Path: {col_meta.path_in_schema}")
            print(f"  Physical Type: {col_meta.physical_type}")
            print(f"  Encodings: {col_meta.encodings}")

    # Load the entire file into memory as a PyArrow Table
    print("\n=== Loading Data ===")
    table = parquet_file.read()

    # Convert the table to a Pandas DataFrame for easier viewing and manipulation
    df = table.to_pandas()

    # Display a preview of the data
    print("\n=== Data Preview (first 5 rows) ===")
    print(df.head())


def main():
    """
    Main function to execute the script.
    Expects the path to a Parquet file as a command line argument.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 load_parquet.py <path_to_parquet_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    load_and_inspect_parquet(filepath)


if __name__ == '__main__':
    main()
