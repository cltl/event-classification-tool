from scipy.signal import find_peaks
from scipy.stats import chi2_contingency
import numpy as np
import polars as pl


def moving_average(df_current_chapter, prompt_for_analysis, window_size=0):
    tags = df_current_chapter[prompt_for_analysis].to_list()
    tags = list(set(tags))
    moving_averages = {tag: [] for tag in tags}
    spans = []

    for i in range(window_size, len(df_current_chapter) + 1):
        # Get the current window
        window = df_current_chapter.slice(i - window_size, window_size)
        
        # Calculate moving averages for each tag
        for tag in tags:
            tag_count = (window[prompt_for_analysis] == tag).sum()
            moving_averages[tag].append(tag_count / window_size)

        # Store the end clause number for this window
        spans.append(i)

    extrema = find_extrema(moving_averages)
    
    return moving_averages, spans


def find_extrema(moving_averages):
    extrema = {}

    for tag, averages in moving_averages.items():
        # Convert the list of averages to a numpy array
        averages_array = np.array(averages)

        # Find indices of relative maxima
        maxima_indices = find_peaks(averages_array)[0]

        # Find indices of relative minima by finding the peaks in the negative of the array
        minima_indices = find_peaks(-averages_array)[0]

        # Store the indices in the extrema dictionary
        extrema[tag] = {'maxima': maxima_indices, 'minima': minima_indices}

    return extrema