from general_functions.match_metadata import *
from general_functions.subtitles import *
from general_functions.clean_book import clean_within_line
from general_functions.match_sections import add_chpt_id

import polars as pl

def book_limits():
    """
    Takes text between START and END
    """
    book_start = r"I do not know what I may appear to the world, but to myself I seem to have been only like a boy playing on the sea-shore, and diverting myself in now and then finding a smoother pebble or a prettier shell than ordinary, whilst the great ocean of truth lay all undiscovered before me. Sir Isaac Newton"# I do not know what I may appear to the world, but to myself I seem to have been only like a boy playing on the sea-shore, and diverting myself in now and then finding a smoother pebble or a prettier shell than ordinary, whilst the great ocean of truth lay all undiscovered before me. Sir Isaac Newton"
    book_end = r"Groningen, sept. '62\[kop\] sept. '65"
    return book_start, book_end

def retrieve_regex():
    """
    Defines the string pattern later used to split the book
    """
    myregex = "Hoofdstuk\s\d+"
    
    return myregex

def add_id_to_sections(df):
    """
    Add an id to each section of the book.
    """
    id_df = add_chpt_id(df)
    return id_df

def match_metadata(df,myregex=None):

    new_df = df
    return new_df

def handle_subtitles(df,myregex):
    return df

def remove_lines(df,myregex):
    """
    Handles removal of metadata
    
    You should add code to remove
    any other line that is not part of the book story,
    which was not captured in match_metadata.
    """
    df_clean = df.filter((pl.col("is_metadata")!= True))

    # add other lines to remove here, if any are present

    return df_clean

def remove_special_chars(df):
    """
    Removes special characters/words that are not part of the book story
    (e.g., notes).
    
    """
    df = df.with_columns(pl.col("lines").str.replace_all("(\[kop\])\s?","-"))

    # Get rid of other special characters, same for all books
    df = clean_within_line(df)

    return df
