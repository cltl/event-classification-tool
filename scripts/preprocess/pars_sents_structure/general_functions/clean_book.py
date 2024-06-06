import polars as pl

def clean_within_line(book_df):
    """
    - Remove "_"
    - Remove "\t" because it will be used as a separator
    - Strip leading and trailing whitespace
    - Remove double spaces
    """
    df = book_df.with_columns(pl.col("lines").str.replace_all("_", " "))
    df = df.with_columns(pl.col("lines").str.replace_all("\t", " "))
    df = df.with_columns(pl.col("lines").str.replace_all("--", " - "))
    df = df.with_columns(pl.col("lines").str.replace_all("—", "-"))
    df = df.with_columns(pl.col("lines").str.replace_all("°", " "))
    df = df.with_columns(pl.col("lines").str.replace_all("\|", " "))
    df = df.with_columns(pl.col("lines").str.strip())
    df = df.with_columns(pl.col("lines").str.replace_all(" +", " "))
    df = df.with_columns(pl.col("lines").str.replace_all(" ,", ","))
    df = df.with_columns(pl.col("lines").str.replace_all(" \.", "."))

    return df