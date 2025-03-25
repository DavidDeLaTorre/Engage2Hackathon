#!/usr/bin/env python3
import glob
import csv
import re
import os

# Directory pattern for the CSV files
input_pattern = "output/training_data/*_statistics.csv"
# Create an output directory for the combined CSV files per runway
output_dir = "output/combined_statistics"
os.makedirs(output_dir, exist_ok=True)

# Regular expression to extract year, month, day, and runway from filenames like:
# "save_2024_11_16_32L_statistics.csv"
filename_pattern = r"save_(\d{4})_(\d{2})_(\d{2})_([^_]+)_statistics\.csv"

# Dictionary to group rows by runway
runway_rows = {}

# Loop over all matching CSV files
for file_path in glob.glob(input_pattern):
    filename = os.path.basename(file_path)
    match = re.match(filename_pattern, filename)
    if not match:
        # Skip files that don't match the expected pattern
        continue
    year, month, day, runway = match.groups()

    # Read the CSV file and build a dictionary mapping statistics to their values
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        stats = {row["Statistic"]: row["Value"] for row in reader}

    # Build the row with date, runway, and statistical values
    row_data = {
        "year": year,
        "month": month,
        "day": day,
        "runway": runway,
        "count": stats.get("count", ""),
        "min": stats.get("min", ""),
        "max": stats.get("max", ""),
        "mean": stats.get("mean", ""),
        "median": stats.get("median", ""),
        "std": stats.get("std", ""),
        "25%": stats.get("25%", ""),
        "75%": stats.get("75%", "")
    }

    # Append the row data under the appropriate runway
    runway_rows.setdefault(runway, []).append(row_data)

# For each runway, sort by date and write a combined CSV file
for runway, rows in runway_rows.items():
    rows.sort(key=lambda x: (x["year"], x["month"], x["day"]))
    output_file = os.path.join(output_dir, f"combined_statistics_{runway}.csv")
    with open(output_file, "w", newline='') as csvfile:
        fieldnames = ["year", "month", "day", "runway", "count", "min", "max", "mean", "median", "std", "25%", "75%"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {output_file}")

print("All combined CSV files have been generated.")
