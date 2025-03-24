import pandas as pd


def compute_segment_delta_times(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes an ADS-B trajectory dataframe and computes the elapsed time (delta_time)
    for each flight segment, returning a new DataFrame with the following fields:
      - icao24 (string)
      - segment (integer identifier)
      - trajectory (string: landing, departing, level)
      - delta_time (in milliseconds; difference between first and last 'ts' in the segment)
      - initial_idx (index of the first row in the original df for this segment)
      - final_idx (index of the last row in the original df for this segment)

    Parameters:
      df (pd.DataFrame): Input dataframe with at least the following columns:
                         'icao24', 'ts', 'segment', 'trajectory'.

    Returns:
      pd.DataFrame: A new DataFrame summarizing the delta time and original index boundaries
                    for each flight segment.
    """
    # List to collect results for each group.
    results = []

    # Group by icao24, segment, and trajectory.
    groups = df.groupby(['icao24', 'segment', 'trajectory'])

    for (icao24, segment, trajectory), group in groups:
        # Ensure that the group is sorted by 'ts' (time in milliseconds).
        group_sorted = group.sort_values('ts')

        # Retrieve the original indexes for the first and last observation in the segment.
        initial_idx = group_sorted.index[0]
        final_idx = group_sorted.index[-1]

        # Compute the elapsed time (delta_time) in milliseconds.
        delta_time = group_sorted['ts'].iloc[-1] - group_sorted['ts'].iloc[0]

        # Append the computed info.
        results.append({
            'icao24': icao24,
            'segment': segment,
            'trajectory': trajectory,
            'delta_time': delta_time / 1000,
            'initial_idx': initial_idx,
            'final_idx': final_idx
        })

    # Return a new DataFrame built from the results list.
    return pd.DataFrame(results)


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def compute_delta_time_statistics(segment_df: pd.DataFrame) -> dict:
    """
    Computes statistics for the 'delta_time' column in the provided DataFrame.

    Parameters:
      segment_df (pd.DataFrame): A DataFrame that must contain a 'delta_time' column.

    Returns:
      dict: A dictionary with statistics including count, min, max, mean, median,
            standard deviation, and the 25th and 75th percentiles.
    """
    delta_times = segment_df['delta_time']
    stats = {
        'count': delta_times.count(),
        'min': delta_times.min(),
        'max': delta_times.max(),
        'mean': delta_times.mean(),
        'median': delta_times.median(),
        'std': delta_times.std(),
        '25%': delta_times.quantile(0.25),
        '75%': delta_times.quantile(0.75)
    }
    return stats


def plot_delta_time_pdf(segment_df: pd.DataFrame, bins: int = 50) -> None:
    """
    Plots the probability density function (PDF) of delta_times from the provided DataFrame.

    Parameters:
      segment_df (pd.DataFrame): A DataFrame containing a 'delta_time' column.
      bins (int): The number of bins to use in the histogram.
    """
    delta_times = segment_df['delta_time']

    plt.figure(figsize=(10, 6))

    # Plot normalized histogram (density=True makes it a PDF)
    counts, bin_edges, _ = plt.hist(delta_times, bins=bins, density=True, alpha=0.6, label='Histogram')

    # Optionally, overlay a kernel density estimate (if scipy is available)
    try:
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(delta_times)
        min_time = delta_times.min()
        max_time = min(500, delta_times.max())
        xs = np.linspace(min_time, max_time, 200)
        plt.plot(xs, kde(xs), 'r-', label='KDE')
    except ImportError:
        # If scipy is not available, we simply skip the KDE overlay.
        pass

    plt.xlabel('Delta Time (ms)')
    plt.ylabel('Probability Density')
    plt.title('PDF of Delta Times')
    plt.legend()
    plt.grid(True)
    plt.show()
