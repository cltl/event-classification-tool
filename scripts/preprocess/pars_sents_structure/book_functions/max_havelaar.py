from general_functions.match_metadata import *
from general_functions.subtitles import *
from general_functions.clean_book import clean_within_line
from general_functions.match_sections import add_chpt_id

import polars as pl

def book_limits():
    """
    Takes text between START and END
    """
    book_start = r"_\(Onuitgegeven Tooneelspel\)_" # write the regex for the book start
    book_end = r"AANTEEKENINGEN EN OPHELDERINGEN" # and end

    return book_start, book_end

def retrieve_regex():
    """
    Defines the string pattern later used to split the book
    """
    myregex = "HOOFDSTUK(\[.+\])?$" # write here the regex to capture the book sections
    
    return myregex

def add_id_to_sections(df):
    """
    Add an id to each section of the book.

    Do
    - id_df = add_chpt_id(df) # If the highest section level is the chapter, e.g., villette.py
    """
    id_df = add_chpt_id(df)
    return id_df

def match_metadata(df,myregex=None):
    """
    Defines the metadata that will be removed from book.
    Can use help functions from chapterize/general_functions/match_metadata
    
    You might want to check in the book stuff like:
    - table of contents
    - notes (in parentheses, square brackets, curly brackets)
    - illustrations
    - a "THE END" line or similar
    - asteristks
    - copyright mentions
    - mentions to later editions
    - page numbers
    - line numbers
    - preface
    - translator notes
    - comments on the book at the end of the book


    """
    new_df = df.with_columns(
            pl.when(
            pl.col("lines").str.contains("(\*\s*){5}") |
            pl.col("lines").str.contains("_{31}")
            )
        .then(True)
        .otherwise(False)
        .alias("is_metadata")
        )
    
    # Notes can span up to 14 lines
    new_df = new_df.with_columns(
            pl.when(
            pl.col("lines").str.starts_with("(*)")
            )
        .then(True)
        .otherwise(False)
        .alias("is_note")
        )

    for x in range(14):
        new_df = new_df.with_columns(
            pl.when(
            (pl.col("char_count")!= 0) &
            (pl.col("is_note").shift(1)== True)
            )
        .then(True)
        .otherwise(pl.col("is_note"))  # preserves existing values where the condition is not met
        .alias("is_note")
        )

    return new_df

def handle_subtitles(df,myregex):
    """
    Defines how many rows after the section form the subtitle.
    Uses functions from chapterize/general_functions/subtitles
    """
    return df

def remove_lines(df,myregex):
    """
    Handles removal of metadata
    
    You should add code to remove
    any other line that is not part of the book story,
    which was not captured in match_metadata.
    """
    df_clean = df.filter((pl.col("is_metadata")!= True))
    df_clean = df_clean.filter(pl.col("is_note") == False)

    return df_clean

def remove_special_chars(df):
    """
    Removes special characters/words that are not part of the book story
    (e.g., notes).
    
    """
    # Remove special characters that are specific to this book
    # df = df.with_columns(pl.col("lines").str.replace_all("[PLACEHOLDER]"," ")) # replace [PLACEHOLDER] with special characters to remove

    # Get rid of other special characters, same for all books
    df = df.with_columns(pl.col("lines").str.replace_all("\*\*\*"," "))
    df = df.with_columns(pl.col("lines").str.replace_all("\[\d+\]"," "))
    df = df.with_columns(pl.col("lines").str.replace_all("\(\*\)"," "))
    df = clean_within_line(df)

    return df
