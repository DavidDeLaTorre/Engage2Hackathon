import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor


df = pd.read_csv("/icarus/code/engage2hackathon/output/test_1week_training.csv")


# ----------------------------
# Train and Save Model Function
# ----------------------------

def train_and_save_model(X, y, model, name):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"\n{name} Results:")
    print("MAE:", mean_absolute_error(y_test, y_pred))
    print("R^2:", r2_score(y_test, y_pred))

    joblib.dump(model, f"{name}_model.pkl")
    print(f"Saved {name} model to models/{name}_model.pkl")

# ----------------------------
# Main Pipeline
# ----------------------------

features = df.drop(columns=['delta_time'])
labels = df['delta_time']

runways = ['32L', '32R', '18L', '18R']

for runway in runways:
    print(f"\nTraining models for Runway {runway}...")
    runway_df = df[df['nearest_runway'] == runway]

    if runway_df.empty:
        print(f"No data available for runway {runway}. Skipping...")
        continue

    features = runway_df.drop(columns=['delta_time', 'icao24', 'nearest_runway'])
    labels = runway_df['delta_time']

    # Random Forest
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    train_and_save_model(features, labels, rf, f"{runway}_random_forest")

    # XGBoost
    xgb = XGBRegressor(n_estimators=100, random_state=42)
    train_and_save_model(features, labels, xgb, f"{runway}_xgboost")

    # LightGBM
    lgb = LGBMRegressor(n_estimators=100, random_state=42)
    train_and_save_model(features, labels, lgb, f"{runway}_lightgbm")
