import pandas as pd
import joblib
import os

# Define the runways and model types
runways = ['32L', '32R', '18L', '18R']
model_types = ['random_forest', 'xgboost', 'lightgbm']

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

# Load the new dataset to predict (assume preprocessed and has 'runway' column)
df_new = pd.read_csv("new_adsb_data.csv")

# Prepare a results list
results = []

# Predict delta_time for each row using corresponding runway models
for index, row in df_new.iterrows():
    runway = row['runway']
    icao24 = row['icao24']
    input_data = row.drop(['runway', 'icao24']).values.reshape(1, -1)

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

