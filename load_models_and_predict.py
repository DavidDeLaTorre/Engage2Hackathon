import glob
import pandas as pd
import joblib
import os


from tools_calculate import get_day_of_week
from tools_filter import clean_dataframe_nulls, sort_dataframe, identify_landing_runway_scenario
from tools_import import load_and_process_parquet_files

results_csv_path = "engage-hackaton-checkpoint/checkpoint_YourTeamName_option1.csv"
base_path = "engage-hackaton-checkpoint"


def process_scenarios(base_path, results_csv_path):
    # Load the checkpoint CSV
    checkpoint_df = pd.read_csv(results_csv_path)

    # Filter only for runways of interest
    allowed_runways = {'18L', '18R', '32L', '32R'}

    def extract_valid_runway(rwy):
        rwy = str(rwy)
        for valid in allowed_runways:
            if valid in rwy:
                return valid
        return None

    checkpoint_df['runway'] = checkpoint_df['runway'].apply(extract_valid_runway)
    checkpoint_df = checkpoint_df[checkpoint_df['runway'].notna()]

    icao24_list = list(checkpoint_df['icao24'].dropna().unique())
    print("Filtered ICAO24s:", icao24_list)

    # Load parquet files that match the filtered ICAO24s
    df_list = []
    folder_paths = glob.glob(f"{base_path}/scenarios/*.parquet")
    for file in folder_paths:
        df = load_and_process_parquet_files(
            [file],
            icao24_list=icao24_list,
            columns_to_extract=['df', 'icao24', 'ts', 'altitude', 'lat_deg', 'lon_deg']
        )
        df_list.append(df)

    combined_df = pd.concat(df_list, ignore_index=True)
    df_filtered = clean_dataframe_nulls(combined_df, ['altitude', 'lat_deg', 'lon_deg'])
    df_sorted = sort_dataframe(df_filtered)

    df_with_runway = df_sorted.merge(
        checkpoint_df[['icao24', 'runway']],
        on='icao24',
        how='left'
    )
    df_with_runway['segment'] = 0
    df_with_runway, basic_info_df, df_segments_ils = identify_landing_runway_scenario(df_with_runway)
    basic_info_df['weekday'] = basic_info_df['ts_fap'].apply(get_day_of_week)

    # Extract hour_of_day from ts_fap (assuming ts_fap is in epoch seconds)
    try:
        basic_info_df['ts_fap'] = pd.to_datetime(basic_info_df['ts_fap'], unit='ms')
        basic_info_df['hour_of_day'] = basic_info_df['ts_fap'].dt.hour
    except Exception as e:
        print("Error processing ts_fap for hour extraction:", e)
        basic_info_df['hour_of_day'] = 0

    df = basic_info_df[['icao24', 'runway_fap', 'ts_fap', 'ts_thr',
                        'distance_fap_to_thr', 'delta_time_fap_to_thr',
                        'speed_fap', 'heading_fap', 'weekday', 'hour_of_day',
                        'distance_scenario']]
    # Add wake vortex index
    wake_df = pd.read_csv('data/wake_vortex_unique.csv')
    df = df.merge(wake_df[['icao24', 'wake_vortex_index']], on="icao24", how="left")
    return df


def load_models(runways, model_types):
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


# Define runways and model types
runways = ['32L', '32R', '18L', '18R']
model_types = ['random_forest', 'xgboost', 'lightgbm']
models = load_models(runways, model_types)

scenario_df = process_scenarios(base_path, results_csv_path)
print("Scenario DataFrame columns:", scenario_df.columns)

# Prepare predictions using the same features used in training
feature_columns = ['distance_fap_to_thr', 'speed_fap', 'heading_fap', 'weekday', 'hour_of_day','wake_vortex_index']
results = []

for index, row in scenario_df.iterrows():
    runway = row['runway_fap']
    icao24 = row['icao24']
    input_data = pd.DataFrame([[row[col] for col in feature_columns]], columns=feature_columns)

    for model_type in model_types:
        model_key = f"{runway}_{model_type}"
        if model_key in models:
            predicted_time = models[model_key].predict(input_data)[0]

            # Scale the predicted time based on the ratio of the new distance_scenario
            # to the original distance_fap_to_thr.
            if row['distance_fap_to_thr'] != 0:
                scale_factor = row['distance_scenario'] / row['distance_fap_to_thr']
            else:
                scale_factor = 1  # Avoid division by zero
            scaled_predicted_time = predicted_time * scale_factor

            results.append({
                'index': index,
                'icao24': icao24,
                'runway': runway,
                'model': model_type,
                'seconds_from_fap_to_threshold': predicted_time,
                'seconds_to_threshold': scaled_predicted_time
            })

results_df = pd.DataFrame(results)
results_df.to_csv("predicted_delta_times.csv", index=False)
print("Saved predictions to predicted_delta_times.csv")

predicted_df = pd.read_csv("predicted_delta_times.csv")
sample_df = pd.read_csv(results_csv_path)
# Step 1: Compute mean predicted seconds_to_threshold per icao24
mean_predictions = predicted_df.groupby("icao24")["seconds_to_threshold"].mean().reset_index()

# Step 2: Merge the mean predictions into the sample_df based on icao24
final_sample_df = sample_df.drop(columns=["seconds_to_threshold"], errors="ignore") \
    .merge(mean_predictions, on="icao24", how="left")

# Save the updated file
output_path = "sample_predictions_filled.csv"
final_sample_df.to_csv(output_path, index=False)