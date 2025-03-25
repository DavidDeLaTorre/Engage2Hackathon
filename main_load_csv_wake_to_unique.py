import pandas as pd

# Load the CSV file
df = pd.read_csv('output/wake_vortex.csv')

# Remove duplicate rows (if you want uniqueness by icao24, specify the subset)
df = df.drop_duplicates(subset='icao24')

# Get the unique values from the 'wake_vortex' column
unique_wake_vortex = df['wake_vortex'].unique()

# Print the unique values
print(unique_wake_vortex)

# Define a mapping for wake_vortex values
# You can adjust the mapping as needed.
wake_mapping = {
    'Heavy':0,
    'Obstruction':1,
    'nan':2,
    '<136,000kg':3,
    '<34,000kg':4,
    'Surface emergency vehicle':5,
    'Rotorcraft':6,
    '<7000kg':7,
    'High vortex':8,
    'Ultralight':9,
    'Reserved':10,
    'Glider':11,
    'Lighter than air':12,
    'High performance':13,
    'Space':14,
    'Surface service vehicle':15,
    'UAM':16,
    'Parachutist':18,
}

# Create a new column with the integer mapping
df['wake_vortex_index'] = df['wake_vortex'].map(wake_mapping)

# Save the DataFrame back to a CSV file
df.to_csv('output/wake_vortex_unique.csv', index=False)
