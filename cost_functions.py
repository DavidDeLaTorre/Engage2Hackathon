#!/usr/bin/env python3

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