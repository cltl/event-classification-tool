"""
Analysis of selected chapters
"""

from general_statistics.moving_avgs import moving_average
from plots import plot_moving_averages
import polars as pl
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from in_out_manager import read_corpus, create_outfolder
from setup import Book

book = Book.fetch_book()

output_folder = book.analysis
create_outfolder(output_folder)
corpusname = f"{book.folder_path}/corpus_sentences.tsv"


def moving_average(df_current_chapter, window_size=0):
    tags = list(set(df_current_chapter["LABEL"].to_list()))
    moving_averages = {tag: [] for tag in tags}
    spans = []

    if window_size>len(df_current_chapter):
        print("Please reduce the window size.")
        sys.exit()

    for i in range(window_size, len(df_current_chapter) + 1):
        # Get the current window
        window = df_current_chapter.slice(i - window_size, window_size)
        
        # Calculate moving averages for each tag
        for tag in tags:
            tag_count = (window["LABEL"] == tag).sum()
            moving_averages[tag].append(tag_count / window_size)

        # Store the end clause number for this window
        spans.append(i)

    return moving_averages, spans

   


if "__main__" == __name__:
    corpus = read_corpus(corpusname)

    hadpicked_chapter = 5
    current_chapter_df = corpus.filter(pl.col("CHAPTER_ID") == hadpicked_chapter)

    # Moving averages over a window of clauses/sentences
    window_size=20
    moving_averages, spans = moving_average(current_chapter_df,window_size)
    plot_moving_averages(moving_averages,spans,hadpicked_chapter,output_folder)
    print(f" >> Output saved in {output_folder}")