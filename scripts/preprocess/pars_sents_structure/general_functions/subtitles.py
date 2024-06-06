import polars as pl

def subtitle_simple(book_df, myregex):
    """
    Subtitle spans only one line
    and is directly after section name (e.g., Chapter) 
    without empty lines
    """
    df_subtitled = book_df.with_columns(
            pl.when(
                (pl.col("lines").shift(1).str.contains(myregex)) &
                (~pl.col("lines").str.contains(myregex)) &
                (pl.col("char_count").shift(-1) == 0)
            )
                
            .then(True)
            .otherwise(False)
            .alias("is_subtitle")
        )
    return df_subtitled

def subtitle_with_newline(book_df,myregex):
    """
    Subtitle can span many lines (up to 5),
    there is one empty line between them and section name
    """
    df_subtitled = book_df.with_columns(
            pl.when(
            (pl.col("char_count").shift(1) == 0) & 
            (pl.col("lines").shift(2).str.contains(myregex))
            )
        .then(True)
        .otherwise(False)
        .alias("is_subtitle")
        )
    for x in range(5):
        df_subtitled = df_subtitled.with_columns(
            pl.when(
            (pl.col("char_count")!= 0) &
            (pl.col("is_subtitle").shift(1)== True)
            )
        .then(True)
        .otherwise(pl.col("is_subtitle"))  # preserves existing values where the condition is not met
        .alias("is_subtitle")
        )

    return df_subtitled