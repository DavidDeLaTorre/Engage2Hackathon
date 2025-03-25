import pandas as pd


def compute_score(*, y_prediction_seconds: list, y_true_seconds: list):
    """Compute score using predicted values and real values.

    The goal is to MINIMIZE the score.
    Predictions above the real value are penalized more than predictions below the real value.

    Args:
        y_prediction_seconds: list of predictions in seconds.
        y_true_seconds: list of real values in seconds.
    """
    if len(y_prediction_seconds) != len(y_true_seconds):
        raise ValueError("The length of the lists must be the same")
    individual_scores = []
    for y_prediction, y_true in zip(y_prediction_seconds, y_true_seconds, strict=True):
        delta = y_prediction - y_true

        if delta >= 0:
            score = pow(abs(delta), 2)
        else:
            score = pow(abs(delta), 1)
        individual_scores.append(score)
    final_score = sum(individual_scores)
    return final_score

real_values = [240.99100017547607, 327.16799998283386]
df_real_values = pd.read_csv('engage-hackaton-checkpoint/checkpoint_solution.csv')
real_values = df_real_values['time_to_threshold_s'].tolist()

df = pd.read_csv('predicted_delta_times.csv')
model_seconds = {
    model: df[df['model'] == model]['seconds_to_threshold'].tolist()
    for model in df['model'].unique()
}
for model in model_seconds:
    score = compute_score(y_prediction_seconds=model_seconds[model], y_true_seconds=real_values)
    print(f"Score of {model} predictions:", score)