import polars as pl

def initial_structure(book_df, module_name):
    """
    Takes text between START and END
    """
    book_start, book_end = module_name.book_limits()

    init_df = book_df.select(
        [
        pl.col("lines"),
        pl.col("lines").str.contains(book_start).alias("book_start"),
        pl.col("lines").str.contains(book_end).alias("book_end"),
        pl.col("lines").str.lengths().alias("char_count")
        ]
        )

    return init_df