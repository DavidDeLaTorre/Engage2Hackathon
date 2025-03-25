#!/usr/bin/env python3
import glob
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Pattern to find the combined CSV files
input_pattern = "output/combined_statistics/*.csv"
csv_files = glob.glob(input_pattern)

for csv_file in csv_files:
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file)

    # Create a new figure for the plot
    plt.figure(figsize=(10, 6))

    # For each row (day) in the DataFrame, compute and plot the normal PDF
    for idx, row in df.iterrows():
        # Get mean and std values (convert to float if needed)
        mean = float(row["mean"])
        std = float(row["std"])

        # Define an x range: from mean - 4*std to mean + 4*std
        x = np.linspace(mean - 4 * std, mean + 4 * std, 200)
        # Compute the normal probability density function (pdf)
        y = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / std) ** 2)

        # Create a label using the date (year-month-day)
        label = f"{row['year']}-{row['month']}-{row['day']}"
        plt.plot(x, y, label=label)

    plt.xlabel("x")
    plt.ylabel("Probability Density")

    # Use the runway value (if present) to title the plot
    if "runway" in df.columns:
        runway = df["runway"].iloc[0]
        plt.title(f"Normal Distribution Functions for Runway {runway}")
    else:
        plt.title("Normal Distribution Functions")

    # Optionally, show the legend if there aren't too many curves
    if len(df) <= 10:
        plt.legend()

    plt.tight_layout()

    # Save the plot with the same path as the csv file but with a .png extension
    png_file = os.path.splitext(csv_file)[0] + ".png"
    plt.savefig(png_file)
    plt.close()

    print(f"Saved plot to {png_file}")

print("All plots have been generated.")
