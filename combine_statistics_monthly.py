#!/usr/bin/env python3
import glob
import os
import pandas as pd

# Pattern to find the combined CSV files per runway
input_pattern = "output/combined_statistics/*.csv"
csv_files = glob.glob(input_pattern)

results = []

for csv_file in csv_files:
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Ensure the columns are floats for the calculations
    df["mean"] = df["mean"].astype(float)
    df["std"] = df["std"].astype(float)

    # Compute the average of the mean and std for the file
    avg_mean = df["mean"].mean()
    avg_std = df["std"].mean()

    # Determine the runway identifier
    # If the "runway" column exists, take its first value; otherwise, extract it from the filename.
    if "runway" in df.columns:
        runway = df["runway"].iloc[0]
    else:
        # Extract runway from a filename like "combined_statistics_32L.csv"
        base = os.path.basename(csv_file)
        parts = base.split("_")
        runway = parts[2].split('.')[0]

    results.append({
        "runway": runway,
        "avg_mean": avg_mean,
        "avg_std": avg_std
    })

# Create a DataFrame from the results and save it to a new CSV file.
output_file = "output/averages.csv"
df_out = pd.DataFrame(results)
df_out.to_csv(output_file, index=False)

print(f"Averages written to {output_file}")
