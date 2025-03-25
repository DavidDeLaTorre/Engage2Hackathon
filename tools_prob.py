import numpy as np

# Function to get N samples greater than the mean
def sample_greater_than_mean(n_samples:int, dist_mean:float, loc:float, scale:float) -> np.ndarray[float]:
    samples: list[float] = []
    while len(samples) < n_samples:
        val = np.random.normal(loc=loc, scale=scale)
        if val > dist_mean:
             samples.append(float(val))

    result = np.array(samples, dtype=float)

    return result

def get_time(runway:str) -> float:
    mean = 0.0
    std_dev = 0.0

    if runway == "32L":
        mean = 129.68137019790453
        std_dev = 9.574605947223727
    elif runway == "32R":
        mean = 200.13922750929368
        std_dev = 13.83752166133672
    elif runway == "18L":
        mean = 222.62294000000003
        std_dev = 11.358378803207032
    elif runway == "18R":
        mean = 287.08779999999996
        std_dev = 12.777681660701294

    return sample_greater_than_mean(1, dist_mean=mean, loc=mean, scale=std_dev)[0]

def get_time_full(scenario_file:str, icao24:str, runway:str) -> float:
    mean = 0.0
    std_dev = 0.0

    if runway == "32L":
        mean = 130.08306116504852
        std_dev = 19.495828938298473
    elif runway == "32R":
        mean = 199.94093323550987
        std_dev = 13.984296004894713
    elif runway == "18L":
        mean = 222.834
        std_dev = 15.012913635211149
    elif runway == "18R":
        mean = 286.3500833333333
        std_dev = 13.354046492344446

    return sample_greater_than_mean(1, dist_mean=mean, loc=mean, scale=std_dev)[0]


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
