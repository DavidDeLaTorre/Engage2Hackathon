import glob

import pandas as pd
import joblib
import os

from tools_filter import clean_dataframe_nulls, sort_dataframe, identify_landing_runway
from tools_import import load_and_process_parquet_files

def process_scenarios(base_path):
    # Load checkpoint CSV
    csv_path = f"{base_path}/samples/sample_predictions_empty.csv"
    checkpoint_df = pd.read_csv(csv_path)

    # Filter to only runways of interest
    allowed_runways = {'18L', '18R', '32L', '32R'}

    # Filter and extract the valid runway
    def extract_valid_runway(rwy):
        rwy = str(rwy)
        for valid in allowed_runways:
            if valid in rwy:
                return valid
        return None

    # Apply filter and normalize runway values
    checkpoint_df['runway'] = checkpoint_df['runway'].apply(extract_valid_runway)
    checkpoint_df = checkpoint_df[checkpoint_df['runway'].notna()]

    # Extract list of ICAO24s
    icao24_list = list(checkpoint_df['icao24'].dropna().unique())
    print("Filtered ICAO24s:", icao24_list)

    # Load parquet files
    df_list = []
    folder_paths = glob.glob(f"{base_path}/samples/*.parquet")
    for file in folder_paths:
        df = load_and_process_parquet_files(
            [file],
            icao24_list=icao24_list,
            columns_to_extract=['df', 'icao24', 'ts', 'altitude', 'lat_deg', 'lon_deg']
        )
        df_list.append(df)

    # Combine, clean, and sort
    combined_df = pd.concat(df_list, ignore_index=True)
    df_filtered = clean_dataframe_nulls(combined_df, ['altitude', 'lat_deg', 'lon_deg'])
    df_sorted = sort_dataframe(df_filtered)

    # Merge in runway info from checkpoint file
    df_with_runway = df_sorted.merge(
        checkpoint_df[['icao24', 'runway']],
        on='icao24',
        how='left'
    )
    df_with_runway['segment'] = 0
    df_with_runway, basic_info_df, df_segments_ils = identify_landing_runway(df_with_runway)

    df = basic_info_df[
        ['icao24', 'runway_fap', 'ts_fap', 'ts_thr',
         'distance_fap_to_thr', 'delta_time_fap_to_thr']
    ].copy()

    return df

def load_models(runways, model_types):
    # Load models into a dictionary
    models = {}
    for runway in runways:
        for model_type in model_types:
            model_path = f"models/{runway}_{model_type}_model.pkl"
            if os.path.exists(model_path):
                models[f"{runway}_{model_type}"] = joblib.load(model_path)
                print(f"Loaded model: {runway}_{model_type}")
            else:
                print(f"Model not found: {runway}_{model_type}")
    return models


# Define the runways and model types
runways = ['32L', '32R', '18L', '18R']
model_types = ['random_forest', 'xgboost', 'lightgbm']
models = load_models(runways, model_types)

scenario_df = process_scenarios('engage-hackaton')
print(scenario_df.columns)
# Prepare a results list
results = []
# Predict delta_time for each row using corresponding runway models
for index, row in scenario_df.iterrows():
    runway = row['runway_fap']
    icao24 = row['icao24']

    # Extract feature as a DataFrame with one row
    input_data = pd.DataFrame([[row['distance_fap_to_thr']]], columns=['distance_fap_to_thr'])

    for model_type in model_types:
        model_key = f"{runway}_{model_type}"
        if model_key in models:
            predicted_time = models[model_key].predict(input_data)[0]
            results.append({
                'index': index,
                'icao24': icao24,
                'runway': runway,
                'model': model_type,
                'seconds_to_threshold': predicted_time
            })
# Convert results to DataFrame and save
results_df = pd.DataFrame(results)
results_df.to_csv("predicted_delta_times.csv", index=False)
print("Saved predictions to predicted_delta_times.csv")

