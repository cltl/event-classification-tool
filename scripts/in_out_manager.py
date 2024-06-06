from datetime import datetime
import polars as pl
import json
import os

def read_book_txt(filename):
    """
    Read a book from a text file
    """
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.rstrip() for line in f]
    
    return lines

def save_df_to_tsv(filename, df):
    """
    Save polars dataframe to tsv
    """
    df.write_csv(filename, separator="\t")

def create_outfolder(saving_folder):
    if not os.path.exists(saving_folder):
        os.makedirs(saving_folder)

def tsv_to_df(infile):
    df = pl.read_csv(infile, separator="\t")

    return df

def read_corpus(corpuspath):
    corpus = pl.read_csv(corpuspath, separator="\t",dtypes={"chapter_id": pl.datatypes.Utf8})
    return corpus