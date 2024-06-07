from general_statistics.distributions import custom_sort, get_chapter_shifts
from general_statistics.basic_stats import counts
from scipy.stats import entropy
import polars as pl
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from story_analysis.plots import plot_entropy


def chapt_entropy(book_df,chapters):
    """
    Entropy of tags per chapter
    """

    entropies = {}
    for chpt in chapters:
        anno_in_chpt = book_df.filter(pl.col("CHAPTER_ID")==chpt)
        tot_spans, tot_S, tot_E, tot_C =counts(anno_in_chpt)
        probs = [tot_S/tot_spans, tot_E/tot_spans, tot_C/tot_spans]
        entrp = entropy(probs,base=10)
        entropies[chpt]=entrp

    return entropies


def chunk_entropy(book_df, num_chunks):
    """
    Calculate the entropy of tags per chunk of the book.
    """
    # Calculate the total number of rows and the size of each chunk
    total_rows = book_df.shape[0]
    chunk_size = total_rows // num_chunks

    entropies = {}

    for i in range(num_chunks):
        # Define the start and end of each chunk
        start_index = i * chunk_size
        # For the last chunk, we take all the remaining rows
        end_index = (i + 1) * chunk_size if i < num_chunks - 1 else total_rows

        # Extract the chunk from the dataframe
        chunk = book_df[start_index:end_index]

        tot_spans, tot_S, tot_E, tot_C = counts(chunk)
        probs = [tot_S, tot_E, tot_C]

        probs = [prob for prob in probs if prob > 0]

        if tot_spans > 0 and len(probs) > 0:  # Ensure we have non-zero data and avoid division by zero
            probs = [prob/tot_spans for prob in probs]  # Normalize probabilities
            entropies[f'chunk_{i+1}'] = entropy(probs, base=10)  # Calculate entropy, specifying the logarithm base if necessary
        else:
            entropies[f'chunk_{i+1}'] = 0  # Handle the case with zero data as you see fit

    return entropies


def e_on_chapters(book_df,entr_folder):
    chapters = book_df["CHAPTER_ID"].unique().to_list()
    chapters = sorted(chapters, key=custom_sort)
    # Entropy of tags per chapt
    entropies = chapt_entropy(book_df,chapters)

    plot_entropy(entropies,f"{entr_folder}/chapter-entropy.pdf")
    

def e_on_chunks(book_df,entr_folder,num_chunks):
    chu_ent = chunk_entropy(book_df, num_chunks)
    # Smooth the numbers using a moving average
    window_size = 6  # Define the size of your moving window

    
    entropy_values = [chu_ent[f'chunk_{i+1}'] for i in range(num_chunks)]
    smoothed_entropies = np.convolve(entropy_values, np.ones(window_size)/window_size, mode='valid')
    smoothed_entropies = {f'chunk_{i+1 + (window_size-1)//2}': value for i, value in enumerate(smoothed_entropies)}

    chapter_boundaries = get_chapter_shifts(book_df,num_chunks)
    plot_entropy(smoothed_entropies,f"{entr_folder}/chunks-entropy-smooth.pdf",nchunks=num_chunks,chapter_boundaries=chapter_boundaries)
    

def do_entropy(corpus,output_folder):

    # Entropy at the chapter level
    e_on_chapters(corpus,output_folder)
        
    # Entropy per chunks of sentences/clauses
    num_chunks = 100
    e_on_chunks(corpus,output_folder,num_chunks)
        