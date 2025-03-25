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

        print(f"score: {score}")
        individual_scores.append(score)
    final_score = sum(individual_scores)
    return final_score

df_real_values = pd.read_csv('engage-hackaton-checkpoint/checkpoint_solution.csv')

#df = pd.read_csv('sample_predictions_filled.csv')
#df = pd.read_csv('results/checkpoint_RAD_option2.csv')
#df = pd.read_csv('results/checkpoint_RAD_option2_new.csv')
df = pd.read_csv('results/checkpoint_RAD_option2_nov_feb.csv')



real_values_seconds = df_real_values['time_to_threshold_s'].tolist()
prediction_values_seconds = df['seconds_to_threshold'].tolist()


score = compute_score(y_prediction_seconds=prediction_values_seconds, y_true_seconds=real_values_seconds)
print(f"Score of  predictions:", score)