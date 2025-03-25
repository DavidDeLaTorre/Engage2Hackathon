import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def compute_segment_delta_times(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes an ADS-B trajectory dataframe and computes the elapsed time (delta_time)
    for each flight segment based on the sub-segment defined by the FAP and threshold.
    Returns a new DataFrame with the following fields:
      - icao24 (string)
      - segment (integer identifier)
      - trajectory (string: landing, departing, level)
      - delta_time (in seconds; difference between FAP and threshold timestamps)
      - initial_idx (index of the FAP row in the original df for this segment)
      - final_idx (index of the threshold row in the original df for this segment)
      - sub_segment_count (optional; number of rows in the sub-segment)

    Assumes that the dataframe contains the columns:
      'icao24', 'ts', 'segment', 'trajectory',
      'idx_fap', 'idx_thr', 'ts_fap', 'ts_thr'.
    """
    results = []

    # Group by icao24, segment, and trajectory.
    groups = df.groupby(['icao24', 'segment', 'trajectory'])

    for (icao24, segment, trajectory), group in groups:
        # Assuming FAP and threshold info is constant within the group,
        # retrieve the FAP and threshold index and timestamp.
        fap_idx = group['idx_fap'].iloc[0]
        thr_idx = group['idx_thr'].iloc[0]
        fap_ts = group['ts_fap'].iloc[0]
        thr_ts = group['ts_thr'].iloc[0]

        # Ensure the group is sorted by timestamp
        group_sorted = group.sort_values('ts')

        # Extract the sub-segment corresponding to times between FAP and threshold.
        # (Assumes fap_ts <= thr_ts; if not, adjust accordingly.)
        sub_segment = group_sorted[(group_sorted['ts'] >= fap_ts) & (group_sorted['ts'] <= thr_ts)]

        # Compute the elapsed time (delta_time) in milliseconds, then convert to seconds.
        delta_time = thr_ts - fap_ts

        results.append({
            'icao24': icao24,
            'segment': segment,
            'trajectory': trajectory,
            'delta_time': delta_time / 1000,  # convert ms to seconds
            'initial_idx': fap_idx,
            'final_idx': thr_idx,
            'sub_segment_count': len(sub_segment)
        })

    return pd.DataFrame(results)


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


def plot_delta_time_pdf(segment_df: pd.DataFrame, bins: int = 50, output_prefix: str = None) -> None:
    """
    Plots the probability density function (PDF) of delta_times from the provided DataFrame.

    Parameters:
      segment_df (pd.DataFrame): A DataFrame containing a 'delta_time' column.
      bins (int): The number of bins to use in the histogram.
    """

    # Extract times
    delta_times = segment_df['delta_time']

    # Min max times for x-axis
    min_time = delta_times.min()
    max_time = min(500, delta_times.max())

    # Cut-out delta-times
    delta_times = delta_times[delta_times < max_time]

    # Figure
    plt.figure(figsize=(10, 6))

    # Plot normalized histogram (density=True makes it a PDF)
    counts, bin_edges, _ = plt.hist(delta_times, bins=bins, density=True, alpha=0.6, label='Histogram')


    # Optionally, overlay a kernel density estimate (if scipy is available)
    try:
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(delta_times)
        xs = np.linspace(min_time, max_time, 200)
        plt.plot(xs, kde(xs), 'r-', label='KDE')
    except ImportError:
        # If scipy is not available, we simply skip the KDE overlay.
        pass

    plt.xlabel('Delta Time (ms)')
    plt.ylabel('Probability Density')
    plt.title('PDF of Delta Times')
    plt.xlim(min_time, max_time)
    plt.legend()
    plt.grid(True)

    # Save the plot if output_prefix is provided, else show the plot
    if output_prefix is not None:
        filename = f"{output_prefix}_delta_time_pdf.png"
        plt.savefig(filename)
        plt.close()
    else:
        plt.show()


# Plot delta_time PDF for each runway
def plot_delta_time_pdf_by_runway(basic_info_df, output_prefix : str = None) -> None:
    # Group the basic_info_df by runway
    for runway, runway_df in basic_info_df.groupby('runway_fap'):
        plt.figure()
        # Plot histogram as a PDF (normalized histogram)
        plt.hist(runway_df['delta_time'], bins=20, density=True, alpha=0.7)
        plt.title(f"Delta Time PDF for Runway {runway}")
        plt.xlabel("Delta Time (seconds)")
        plt.ylabel("Density")
        plt.grid(True)

        # Save or display the plot
        if output_prefix is not None:
            filename = f"{output_prefix}_runway_{runway}_delta_time_pdf.png"
            plt.savefig(filename)
            plt.close()
        else:
            plt.show()
def find_outliers(basic_info_df):
    for runway, runway_df in basic_info_df.groupby('runway_fap'):
        outliers = runway_df[runway_df['delta_time'] < 165]
        #date_str = datetime.datetime.fromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')
        print(runway, len(outliers))
        for icao24, ts_fap in zip(outliers["icao24"], outliers["ts_fap"]):
            date_str = datetime.datetime.fromtimestamp(ts_fap/1000).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{icao24}\t{date_str}")