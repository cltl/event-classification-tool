import polars as pl

def define_regex_sections(book_df, myregex):
    """
    Sets value true where regex for the sections matched
    Sets section values (e.g., chapter number)
    """
    match_sections = book_df.with_columns(
    [
    pl.col("lines"),
    pl.col("lines").str.contains(myregex).alias("section_start"),
    ]
    )
    return match_sections

def match_body(df):
    """
    Sets as section 0 all that is before or after book start/end
    i.e., *** START/END OF THE PROJECT GUTENBERG EBOOK...
    (section 0 will be removed)
    """
    row_number = pl.Series("row_number", list(range(df.shape[0])))
    df = df.with_columns(row_number)

    # Rows where 'book_start' or 'book_end' is True
    df_book_boundaries = df.filter(pl.col("book_start") | pl.col("book_end"))
    df_book_boundaries = df_book_boundaries.select(["book_start", "book_end", "row_number"])

    # Identify 'book_start' and 'book_end' row numbers
    book_start_row = df_book_boundaries.filter(pl.col("book_start"))["row_number"][0]
    book_end_row = df_book_boundaries.filter(pl.col("book_end"))["row_number"][0]

    # Get when only rows within the boundaries (exclusive) are True
    body = (df['row_number'] > book_start_row) & (df['row_number'] < book_end_row)

    return body, df


def add_chpt_id(book_df):
    """
    Numbers chapters sequentially

    """
    df = book_df.with_columns(
        pl.col("lines"),
        pl.col("section_start").cumsum().alias("chapter_id")
        )

    body,df = match_body(df)

    # Update 'section_id' in the dataframe
    df = df.with_columns(
        pl.when(body).then(df['chapter_id']).otherwise(0).alias('chapter_id'))

    return df