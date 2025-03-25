import glob
import pandas as pd
import joblib
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

# ----------------------------
# Data Loading & Combination
# ----------------------------

csv_files = glob.glob('/icarus/code/engage2hackathon/data/training_november/*.csv')
csv_files += glob.glob('/icarus/code/engage2hackathon/data/training_december/*.csv')
csv_files += glob.glob('/icarus/code/engage2hackathon/data/training_january/*.csv')
csv_files += glob.glob('/icarus/code/engage2hackathon/data/training_february/*.csv')
print("CSV Files found:", csv_files)

# Load and combine CSV files into one DataFrame
df_list = [pd.read_csv(file) for file in csv_files]
df = pd.concat(df_list, ignore_index=True)

# ----------------------------
# Feature Engineering
# ----------------------------
# Convert ts_fap (assumed to be in epoch seconds) into datetime and extract hour_of_day.
try:
    df['ts_fap'] = pd.to_datetime(df['ts_fap'], unit='s')
    df['hour_of_day'] = df['ts_fap'].dt.hour
except Exception as e:
    print("Error converting ts_fap:", e)
    df['hour_of_day'] = 0  # default value if conversion fails

#Add wake vortex index
wake_df = pd.read_csv('/icarus/code/engage2hackathon/data/wake_vortex_unique.csv')
df = df.merge(wake_df[['icao24', 'wake_vortex_index']], on="icao24", how="left")


# (Optional) You may drop ts_fap if not needed later:
# df.drop(columns=['ts_fap'], inplace=True)

# ----------------------------
# Improved Training Function with Pipeline & Hyperparameter Tuning
# ----------------------------
def train_and_save_model_improved(X, y, model, name, param_grid=None):
    # Build a preprocessing + model pipeline:
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),  # Robust imputation
        ('scaler', StandardScaler()),  # Feature scaling
        ('model', model)
    ])

    # Hyperparameter tuning if parameters are provided
    if param_grid:
        grid = GridSearchCV(pipeline, param_grid, cv=3, scoring='neg_mean_absolute_error', n_jobs=-1)
        grid.fit(X, y)
        best_model = grid.best_estimator_
        print(f"{name} best parameters: {grid.best_params_}")
    else:
        pipeline.fit(X, y)
        best_model = pipeline

    # Evaluate using a hold-out test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    best_model.fit(X_train, y_train)
    y_pred = best_model.predict(X_test)

    print(f"\n{name} Results:")
    print("MAE:", mean_absolute_error(y_test, y_pred))
    print("R^2:", r2_score(y_test, y_pred))

    # Save the trained model
    joblib.dump(best_model, f"{name}_model.pkl")
    print(f"Saved {name} model to models/{name}_model.pkl")


# ----------------------------
# Main Training Pipeline
# ----------------------------
# Define the features to use; note the new 'hour_of_day' feature is added
feature_columns = ['distance_fap_to_thr', 'speed_fap', 'heading_fap', 'weekday', 'hour_of_day','wake_vortex_index']

runways = ['32L', '32R', '18L', '18R']
for runway in runways:
    print(f"\nTraining models for Runway {runway}...")
    runway_df = df[df['runway_fap'] == runway]
    if runway_df.empty:
        print(f"No data available for runway {runway}. Skipping...")
        continue

    # Check that required columns exist
    missing_cols = [col for col in feature_columns if col not in runway_df.columns]
    if missing_cols:
        print(f"Missing columns {missing_cols} for runway {runway}. Skipping...")
        continue

    # Prepare training data
    features = runway_df[feature_columns]
    labels = runway_df['delta_time_fap_to_thr']

    # --- Random Forest with hyperparameter tuning ---
    rf = RandomForestRegressor(random_state=42)
    rf_param_grid = {
        'model__n_estimators': [100, 200],
        'model__max_depth': [None, 10, 20],
    }
    train_and_save_model_improved(features, labels, rf, f"{runway}_random_forest", rf_param_grid)

    # --- XGBoost (default parameters for brevity) ---
    xgb = XGBRegressor(random_state=42, n_estimators=100)
    train_and_save_model_improved(features, labels, xgb, f"{runway}_xgboost")

    # --- LightGBM (default parameters for brevity) ---
    lgb = LGBMRegressor(random_state=42, n_estimators=100)
    train_and_save_model_improved(features, labels, lgb, f"{runway}_lightgbm")
