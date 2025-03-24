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
        mean = 128.43645969884855
        std_dev = 319.08290992563684
    elif runway == "32R":
        mean = 214.94028219971054
        std_dev = 310.3969762852255
    elif runway == "18L":
        mean = 142.61910344827587
        std_dev = 307.98815630923383
    elif runway == "18R":
        mean = 56.72466666666662
        std_dev = 775.7244857238451

    return sample_greater_than_mean(1, dist_mean=mean, loc=mean, scale=std_dev)[0]
