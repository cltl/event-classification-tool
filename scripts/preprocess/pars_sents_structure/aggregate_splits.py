import polars as pl
import sys
import os


def group_paragraphs(df):

    # Filter out rows where 'lines' column is empty
    df = df.filter(pl.col("lines") != "")

    # Create a new 'paragraph_id' column and
    df = df.with_columns(
        pl.col("paragraph_start").cumsum().alias("paragraph_id")
    )

    # Filter out the chapter titles and subtitles
    df = df.filter(
        (pl.col("section_start")==False) &
        (pl.col("is_subtitle")==False)
    )

    # Perform the group by operations
    grouped = df.groupby('paragraph_id')
    df_grouped = grouped.agg(
        [   
            pl.col("lines").apply(' '.join, return_dtype=pl.Utf8).alias("lines"),
            pl.col("char_count").sum().alias("char_count"),
            pl.col("chapter_id").first().alias("chapter_id")
        ]
        )

    # Sorting the dataframe by paragraph_id
    df_grouped = df_grouped.sort("paragraph_id")

    df_grouped = df_grouped.rename({"lines": "paragraphs"})
    
    outdf = df_grouped.drop(["char_count"])
   
    return df_grouped