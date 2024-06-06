from general_statistics.basic_stats import counts
import polars as pl
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from story_analysis.plots import plot_tag_distribution


def custom_sort(item):

    return (1, int(item))
    

def chapt_distr(book_df):
    """
    Relative frequency of a tag in a chapter
    (normalized by the number of clauses in the chapter)
    """
    chapters = book_df["CHAPTER_ID"].unique().to_list()
    chapters = sorted(chapters, key=custom_sort)

    distributions = {"S":[], "E":[], "C":[]}

    for chpt in chapters:
        anno_in_chpt = book_df.filter(pl.col("CHAPTER_ID")==chpt)

        tot_spans, tot_S, tot_E, tot_C =counts(anno_in_chpt)
        denominator = tot_spans

        round_S = round(tot_S/denominator,2)
        round_E = round(tot_E/denominator,2)
        round_C = round(tot_C/denominator,2)

        distributions["S"].append(round_S)
        distributions["E"].append(round_E)
        distributions["C"].append(round_C)
    
    return distributions


def calculate_moving_average(data, window_size):
    """
    Calculate the moving average for the input data.
    :param window_size: Number of data points to consider for each moving average calculation.
    
    Returns smoothed data as a list.
    """
    if window_size > len(data):
        raise ValueError("Window size must be less than or equal to the data size.")
    
    # Precompute cumulative sums
    cumsum = [0]
    for i, value in enumerate(data, 1):
        cumsum.append(cumsum[i - 1] + value)

    # Calculate moving averages using the cumulative sums
    moving_averages = []
    for i in range(len(data) - window_size + 1):
        average = (cumsum[i + window_size] - cumsum[i]) / window_size
        moving_averages.append(average)

    return moving_averages



def chunk_distr(book_df, num_chunks):
    """
    Calculate the relative frequency of a tag in a chunk of the book (normalized by the number of clauses in the chunk).
    num_chunks: Number of chunks to split the book into.
    
    Returns dictionary containing distributions for each tag.
    """
    # Calculate the size of each chunk
    total_rows = book_df.shape[0]
    chunk_size = total_rows // num_chunks

    # Prepare the dictionary for the distributions
    distributions = {"S": [], "E": [], "C": []}

    for i in range(num_chunks):
        # Define the start and end of each chunk
        start_index = i * chunk_size
        # For the last chunk, we take all the remaining rows
        end_index = (i + 1) * chunk_size if i < num_chunks - 1 else total_rows

        # Extract the chunk from the dataframe
        chunk = book_df[start_index:end_index]

        # Calculate the counts for each tag in the current chunk
        # (assuming a 'counts' function exists or is provided)
        tot_spans, tot_S, tot_E, tot_C = counts(chunk)
        denominator = tot_spans

        # To avoid division by zero, check if the denominator is zero and handle it
        if denominator == 0:
            round_S = round_E = round_C = 0
        else:
            round_S = round(tot_S / denominator, 2)
            round_E = round(tot_E / denominator, 2)
            round_C = round(tot_C / denominator, 2)

        # Append the results to our distributions
        distributions["S"].append(round_S)
        distributions["E"].append(round_E)
        distributions["C"].append(round_C)

    return distributions


    
def on_chapter(book_df,dist_folder):
    chapter_distribution = chapt_distr(book_df)
    
    plot_tag_distribution(chapter_distribution,f"{dist_folder}/chapter_distribution.pdf",unit="Chapter")
    


def normalize_chapter_boundaries(chapter_change_indices, total_rows, num_chunks):

    # Normalizing chapter transitions to the plot scale
    normalized_transitions = [(index * num_chunks) // total_rows + 1 for index in chapter_change_indices]
    # Ensure the last transition point is not beyond the plot
    normalized_transitions = [min(num_chunks, transition) for transition in normalized_transitions]
    
    return normalized_transitions




def get_chapter_shifts(book_df,num_chunks):
    previous_chapter = book_df['CHAPTER_ID'].shift(1)
    book_df = book_df.with_columns((book_df['CHAPTER_ID'] != previous_chapter).alias('new_chapter'))
    # Add a row enumeration, effectively creating an 'index'
    book_df = book_df.with_columns(pl.arange(0, book_df.shape[0]).alias('row_number'))

    # Filter rows where 'new_chapter' is True, then select only the 'row_number' column
    chapter_change_rows = book_df.filter(book_df['new_chapter']).select(pl.col('row_number'))

    chapter_change_indices = chapter_change_rows['row_number'].to_list()

    normalized_shifts = normalize_chapter_boundaries(chapter_change_indices, book_df.shape[0], num_chunks)
    return normalized_shifts



def on_chunk(book_df, dist_folder, num_chunks=100):
    chunk_dist = chunk_distr(book_df, num_chunks)

    # Smooth the distributions using a moving average
    smoothed_distributions = {}
    window_size = 6  # Define the size of your moving window

    for tag, values in chunk_dist.items():
        # Smooth the distribution for the current tag
        smoothed_values = calculate_moving_average(values, window_size)
        smoothed_distributions[tag] = smoothed_values

    chapter_boundaries = get_chapter_shifts(book_df,num_chunks)

    plot_tag_distribution(smoothed_distributions,f"{dist_folder}/chunk-distribution-smooth.pdf",unit="Textual Chunk",chapter_boundaries=chapter_boundaries)



def do_distribution(corpus,output_folder):

    # Distribution per chapter
    on_chapter(corpus,output_folder)
    
    # Distributin per chunk
    on_chunk(corpus,output_folder,num_chunks=100)
    