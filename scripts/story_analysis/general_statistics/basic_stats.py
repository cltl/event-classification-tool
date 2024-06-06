"""
Counts S, E and C clauses in the book
"""
import polars as pl
import itertools
import sys
import os

script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir,os.path.pardir))
sys.path.append(script_dir)
from story_analysis.plots import barplot_tags



def counts(anno_df):
    """
    Number of each tag
    """
    tot_spans = len(anno_df)
    tot_S = anno_df.filter(pl.col("LABEL")=="S").shape[0]
    tot_E = anno_df.filter(pl.col("LABEL")=="E").shape[0]
    tot_C = anno_df.filter(pl.col("LABEL")=="C").shape[0]

    return tot_spans, tot_S, tot_E, tot_C


def do_stats(corpus,output_folder):
    """
    Number of each tag divided by the total number of tagged spans
    """
    lengths_tags = {"S":[], "E":[], "C":[]}
    tot_spans, tot_S, tot_E, tot_C =counts(corpus)
    prop_s, prop_e, prop_c = round(tot_S/tot_spans,2) ,round(tot_E/tot_spans,2), round(tot_C/tot_spans,2)
    
    counts_tags = {"S":tot_S, "E": tot_E, "C": tot_C}
    props = {"S":prop_s, "E":prop_e, "C":prop_c}
        
    # Plot counts normalized by number of clauses in book
    print(f"   - raw counts: {counts_tags}")
    print(f"   - relative frequency: {props}")
    barplot_tags(counts_tags,f"{output_folder}/tags_in_books.pdf")
    
