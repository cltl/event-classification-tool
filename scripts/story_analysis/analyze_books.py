from __future__ import division
from general_statistics.basic_stats import do_stats
from general_statistics.distributions import do_distribution
from general_statistics.entropies import do_entropy
import polars as pl

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from setup import Book
from in_out_manager import read_corpus, create_outfolder

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--sentences', action='store_true', help='Analyzes the annotation of the sentences of the book.')
parser.add_argument('--clauses', action='store_true', help='Analyzes the annotation of the clauses of the book.')
args = parser.parse_args()

book = Book.fetch_book()


if args.sentences:
    corpusname = f"{book.folder_path}/corpus_sentences.tsv"
    output_folder = f"{book.analysis}/sentences"
else:
    corpusname = f"{book.folder_path}/corpus_clauses.tsv"
    output_folder = f"{book.analysis}/clauses"
create_outfolder(output_folder)


if __name__=="__main__":
    corpus = read_corpus(corpusname)

    print(" \u2022 Analyzing basic stats on S, E and C clauses:")
    do_stats(corpus,output_folder)

    print(" \u2022 Analyzing distributions.")
    do_distribution(corpus,output_folder)
    
    print(" \u2022 Analyzing entropy.")
    do_entropy(corpus,output_folder)
    
    print(f"\n\u2713 All outputs saved in {output_folder}")