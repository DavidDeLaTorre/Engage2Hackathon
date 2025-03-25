import pandas as pd
import glob

def extract_and_save_wake_vortex(filepath: str) -> pd.DataFrame:
    df = pd.read_parquet(filepath)

    # Filter rows where 'wake_vortex' is neither NaN nor an empty string.
    filtered_df = df[df['wake_vortex'].notna() & (df['wake_vortex'] != '')].copy()

    # Extract the columns 'icao24' and 'wake_vortex'
    result_df = filtered_df[['icao24', 'wake_vortex']]

    # Get only the unique pairs
    result_df_unique = result_df.drop_duplicates(subset=['icao24', 'wake_vortex'])

    return result_df_unique

files = glob.glob('data/engage-hackathon-2025/*/*/*/*/*.parquet')
df_list = []

for file in files:
    df_temp = extract_and_save_wake_vortex(file)

    df_list.append(df_temp)
    print(file + " Done!")

all_df = pd.concat(df_list)
# Save the resulting dataframe to a CSV file.
all_df.to_csv("output/wake_vortex.csv", index=False)
