import polars as pl


def mark_illustrations(book_df):
    # Define illustration_id
    df = book_df.with_columns(pl.when(pl.col("illustration")).then(pl.col("illustration").cumsum())
        .when(pl.col("end_bracket")).then(pl.col("illustration").cumsum())
        .otherwise(None).alias("illustration_id"))

        
    df_no_nulls = df.filter(pl.col("illustration_id").is_not_null())

    illustration_range_df = df_no_nulls.groupby("illustration_id").agg(
        [
            pl.col("row_number").min().alias("start_row"),
            pl.col("row_number").max().alias("end_row"),
        ]
        )
    illustration_range_df = illustration_range_df.sort("illustration_id")
    
    # Initialize df where illustration_id is given
    # to all rows within [Illustration brackets]
    df_filled = df.clone()
    for row in illustration_range_df.rows():
        illustration_id, start_row, end_row = row

        # Create a mask between start_row and end_row
        mask = (df_filled['row_number'] >= start_row) & (df_filled['row_number'] <= end_row)

        # Fill it with the current illustration_id
        df_filled = df_filled.with_columns(pl.when(mask).then(illustration_id).otherwise(df_filled['illustration_id']).alias('illustration_id'))
    
    new_df = df_filled.clone()

    return new_df
