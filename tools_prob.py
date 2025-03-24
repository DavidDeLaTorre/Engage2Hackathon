import numpy as np

# Function to get N samples greater than the mean
def sample_greater_than_mean(n_samples:int, dist_mean:float, loc:float, scale:float):
    samples = []
    while len(samples) < n_samples:
        val = np.random.normal(loc=loc, scale=scale)
        if val > dist_mean:
             samples.append(val)
    return np.array(samples)

def get_time(runway:str) -> float:
    if runway == "32L":
        mean = 122.55961864406778
        std_dev = 17.136927781179246
    elif runway == "32R":
        mean = 206.44466229508197
        std_dev = 215.23136246231007
    elif runway == "18L":
        mean = 142.61910344827587
        std_dev = 307.98815630923383
    elif runway == "18R":
        mean = 56.72466666666662
        std_dev = 775.7244857238451

    return sample_greater_than_mean(1, dist_mean=mean, loc=mean, scale=std_dev)[0]
