#!/usr/bin/env python3
"""
ADS-B Runway Safety Analysis Script

This script loads a single ADS-B Parquet file and performs a statistical analysis
with a focus on runway safety. The analysis assumes that aircraft in the approach
or landing phase (i.e. near the runway) have an altitude below 2000 ft. The script:
    - Loads the Parquet file using PyArrow.
    - Converts the data into a Pandas DataFrame.
    - Filters the dataset for low-altitude (landing/approach) records.
    - Computes summary statistics and correlations for key parameters.
    - Generates plots (histograms, scatter plots, and a correlation heatmap)
      to visualize distributions and relationships relevant to runway safety.

This script serves as a tutorial on how to process, manipulate, and visualize ADS-B data.
"""

import sys
import pyarrow.parquet as pq
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def load_parquet_file(filepath):
    """
    Load a Parquet file and convert it to a Pandas DataFrame.

    Args:
        filepath (str): Path to the Parquet file.

    Returns:
        pd.DataFrame: Loaded ADS-B data.
    """
    try:
        # Open the Parquet file with PyArrow
        parquet_file = pq.ParquetFile(filepath)
        # Read the entire file into a PyArrow Table
        table = parquet_file.read()
        # Convert the table to a Pandas DataFrame
        df = table.to_pandas()
        return df
    except Exception as e:
        print(f"Error loading file {filepath}: {e}")
        sys.exit(1)


def preprocess_data(df):
    """
    Preprocess the ADS-B data for runway safety analysis.

    In this context, we assume that flights with altitude below 2000 ft
    are in their approach/landing phase and are thus more relevant for runway safety.

    Args:
        df (pd.DataFrame): The ADS-B data.

    Returns:
        pd.DataFrame: Filtered data focusing on the approach/landing phase.
    """
    # Convert relevant columns to numeric (in case they were read as objects)
    df['altitude'] = pd.to_numeric(df['altitude'], errors='coerce')
    df['vertical_rate'] = pd.to_numeric(df['vertical_rate'], errors='coerce')
    df['groundspeed'] = pd.to_numeric(df['groundspeed'], errors='coerce')

    # Filter rows with altitude below 2000 ft (approximate landing/approach phase)
    landing_df = df[df['altitude'] < 2000].copy()

    # Drop rows where altitude or vertical_rate is missing (essential for safety analysis)
    landing_df = landing_df.dropna(subset=['altitude', 'vertical_rate'])

    return landing_df


def perform_statistical_analysis(df):
    """
    Perform statistical analysis on key parameters related to runway safety.

    Prints summary statistics (mean, std, percentiles) and calculates the
    correlation matrix for parameters like altitude, vertical_rate, and groundspeed.

    Args:
        df (pd.DataFrame): Filtered ADS-B data (landing phase).

    Returns:
        pd.DataFrame: Correlation matrix of key parameters.
    """
    print("Summary Statistics for Approach/Landing Phase:")
    stats = df[['altitude', 'vertical_rate', 'groundspeed']].describe()
    print(stats)

    # Compute correlations between altitude, vertical rate, and groundspeed
    corr_matrix = df[['altitude', 'vertical_rate', 'groundspeed']].corr()
    print("\nCorrelation Matrix:")
    print(corr_matrix)

    return corr_matrix


def plot_histogram(df, column, bins=50):
    """
    Plot a histogram for a specified column.

    Args:
        df (pd.DataFrame): Dataframe containing the data.
        column (str): Column name to plot.
        bins (int): Number of bins for the histogram.
    """
    plt.figure(figsize=(8, 6))
    plt.hist(df[column].dropna(), bins=bins, edgecolor='black', alpha=0.7)
    plt.title(f'Histogram of {column}')
    plt.xlabel(column)
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_scatter(df, x_col, y_col):
    """
    Plot a scatter plot for two specified columns.

    Args:
        df (pd.DataFrame): Dataframe containing the data.
        x_col (str): Column name for the x-axis.
        y_col (str): Column name for the y-axis.
    """
    plt.figure(figsize=(8, 6))
    plt.scatter(df[x_col], df[y_col], alpha=0.5)
    plt.title(f'Scatter Plot: {y_col} vs. {x_col}')
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_correlation_heatmap(corr_matrix):
    """
    Plot a heatmap of the correlation matrix using matplotlib.

    Args:
        corr_matrix (pd.DataFrame): Correlation matrix.
    """
    plt.figure(figsize=(6, 5))
    # Use imshow to display the correlation matrix
    im = plt.imshow(corr_matrix, cmap='viridis', interpolation='none')
    plt.colorbar(im)
    # Set tick labels
    plt.xticks(ticks=np.arange(len(corr_matrix.columns)), labels=corr_matrix.columns, rotation=45, ha='right')
    plt.yticks(ticks=np.arange(len(corr_matrix.index)), labels=corr_matrix.index)
    plt.title('Correlation Heatmap')
    plt.tight_layout()
    plt.show()


def main():
    """
    Main function to execute the runway safety analysis:
      1. Loads the ADS-B Parquet file.
      2. Preprocesses the data to focus on landing phase (altitude < 2000 ft).
      3. Performs statistical analysis.
      4. Generates visualizations to aid in understanding the data.

    The script expects the path to a Parquet file as a command line argument.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 adsb_runway_safety_analysis.py <path_to_parquet_file>")
        sys.exit(1)

    filepath = sys.argv[1]

    # Step 1: Load the data
    print("Loading ADS-B data...")
    df = load_parquet_file(filepath)

    # Step 2: Preprocess data (filter for landing/approach phase)
    print("Preprocessing data for runway safety analysis (altitude < 2000 ft)...")
    landing_df = preprocess_data(df)
    print(f"Records in landing phase: {len(landing_df)}")

    # Step 3: Statistical analysis of key safety parameters
    corr_matrix = perform_statistical_analysis(landing_df)

    # Step 4: Generate plots for a comprehensive analysis

    # Histogram for altitude distribution in the landing phase
    plot_histogram(landing_df, 'altitude', bins=50)

    # Histogram for vertical_rate distribution
    plot_histogram(landing_df, 'vertical_rate', bins=50)

    # Scatter plot to inspect the relationship between altitude and vertical_rate
    plot_scatter(landing_df, 'altitude', 'vertical_rate')

    # Scatter plot to inspect the relationship between altitude and groundspeed
    plot_scatter(landing_df, 'altitude', 'groundspeed')

    # Plot correlation heatmap for key parameters
    plot_correlation_heatmap(corr_matrix)


if __name__ == '__main__':
    main()
