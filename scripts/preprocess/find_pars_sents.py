"""
Splits books into chapters and paragraphs
and saves the result in outputs/books
"""
from mytokenizers import tok_sentences_df
import polars as pl
import importlib
import sys
import os
import re

script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.append(script_dir)
from in_out_manager import read_book_txt

from pars_sents_structure.general_functions.initial_structure import initial_structure
from pars_sents_structure.general_functions.match_sections import define_regex_sections
from pars_sents_structure.general_functions.handle_quotes import QuoteConverter

folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "pars_sents_structure"))
sys.path.append(folder_path)


def list_to_df(book_lines):
    """
    All operations are done on this polar dataframe
    """
    df = pl.DataFrame({
        'lines': book_lines
    })

    return df

def slim_dataframe(structured_book):
    """
    Select columns in the df that will be saved
    """

    cols = ["lines",
            "chapter_id",
            "section_start", 
            "paragraph_start",
            "is_subtitle",
            "char_count"
            ]
    
    out = structured_book.select(cols)

    return out


def paragraphize(book_df,myregex):
    """
    Cut paragraph where there is empty line
    """
    df_pars = book_df.with_columns(
    pl.when(
        (pl.col("char_count").shift(1) == 0) &
        (pl.col("char_count") != 0) &
        (pl.col("is_subtitle")== False) &
        (~pl.col("lines").str.contains(myregex)) 
        )
        .then(1)
        .otherwise(0)
        .alias("paragraph_start")
    )

    return df_pars


def split_book(book_df,module_name):
    """
    Returns a polar dataframe with the book split into paragraphs
    """

    # Import book modules dynamically
    try:
        module = importlib.import_module(module_name)

    except ImportError:
        print(f"Error: Failed to import {module_name}.")
        print(f"Please make sure that {module_name} exists.\n")
        sys.exit(1)

    # Define where body starts and ends
    init_df = initial_structure(book_df, module)

    # Splits sections based on regex
    myregex = module.retrieve_regex()
    matched_sections = define_regex_sections(init_df, myregex)
    sections_with_id = module.add_id_to_sections(matched_sections)
    

    # Define metadata that will be removed from book
    init_meta = sections_with_id.with_columns(
        pl.lit(False).alias("is_metadata"))
    df_with_meta = module.match_metadata(init_meta,myregex)
    
    # Mark subtitles
    df_sub = df_with_meta.with_columns(
        pl.lit(False).alias("is_subtitle"))
    df_sub = module.handle_subtitles(df_sub,myregex)

    # Split into paragraphs where there is empty line
    split_df = paragraphize(df_sub,myregex)
    
    # Remove useless lines, e.g.:
    # empty, with metadata, illustrations, chapter_id 0, 
    df_clean = module.remove_lines(split_df,myregex)


    slim_df = df_clean.filter(
        (pl.col("chapter_id") != 0) &
        (pl.col("char_count") != 0))

    # Clean the lines
    clean_lines = module.remove_special_chars(slim_df)
    

    # Count chars again after cleaning
    out = clean_lines.with_columns(
        [
        pl.col("lines"),
        pl.col("lines").str.len_bytes().alias("char_count")
        ]
        )


    # Recompute section id after cleaning
    out_df = out.with_columns(
        pl.col("lines"),
        pl.col("section_start").cum_sum().alias("chapter_id")
        )


    return out_df


def customized_paragraphs(title,formatted_texts):
    """
    For those books in which paragraphs are indicated by special symbols
    """
    if title.lower() in ["nooit meer slapen","sadistisch universum"]:
        ft = []
        for ind,t in enumerate(formatted_texts):
            if "[witregel] ..........." in t:
                continue 
            markers_start = "^\s?[^a-zA-Z]?\s?\[?\s?[^a-zA-Z]\s?witregel\s?[^a-zA-Z]?\]\s?[^a-zA-Z]?"
            markers_end = "\[witregel\]$"
            
            if not re.search("\s?[^a-zA-Z]?\s?\[?\s?[^a-zA-Z]\s?witregel\s?[^a-zA-Z]?\]\s?[^a-zA-Z]?",t):
                ft.append(t)
            else: # indicates new paragraph
                if re.search(markers_start,t): # in Nooit Meer Slapen
                    ft.append("")
                    newt =re.sub(markers_start,"",t)
                    if not re.search(markers_end,newt):
                        ft.append(newt)
                    else:
                        ft.append(re.sub(markers_end,"",newt))
                        ft.append("")
                    
        formatted_texts = ft
    
    if title=="Paranoia":
        ft = []
        for ind,t in enumerate(formatted_texts):
            if t.startswith("»"):
                ft[ind-1] = ft[ind-1]+"»"
                ft.append(re.sub("»","",t))
            elif re.search("[IVX]\s?$",t):
                ft.append(re.sub("[IVX]\s?$","",t)) # indicates new paragraph
            else:
                ft.append(t)
        formatted_texts = ft

    return formatted_texts


def preprocess_abook(book):

    book_lines = read_book_txt(book.txt_filename)

    # Make quotes consistent (use curly brackets)
    converter = QuoteConverter()
    formatted_texts = [converter.replace_with_curly_quotes(t) for t in book_lines]
    formatted_texts = customized_paragraphs(book.title,formatted_texts)

    # Convert to polar dataframe
    book_df = list_to_df(formatted_texts)

    # Paragraphize book
    module_name = f"book_functions.{book.folder_name}"
    structured_book = split_book(book_df,module_name)
        
    # Drop useless cols from dataframe
    final_df = slim_dataframe(structured_book)


    return final_df

def par_to_sents(par_df):
    df_with_sents = tok_sentences_df(par_df)

    sents_df = (
        df_with_sents.with_columns(pl.col("sentences").str.split("\n"))
        .explode("sentences")
        .with_row_count("sentence_id")
        .with_columns((pl.col("sentence_id") + 1).alias("sentence_id"))
        )

    # Display the sents_df DataFrame
    sents_df= sents_df.drop(["paragraphs", "char_count"])

    return sents_df
    

