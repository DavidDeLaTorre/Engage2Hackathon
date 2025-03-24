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
