import polars as pl
import json
import os




def annotations_to_tsv(book,column):
    annotation_jsons_dir = f"{book.annotation_folder}/{column}"

    # Open all files in the annotation_jsons_dir and load the JSON data
    all_annotations = []
    for filename in os.listdir(annotation_jsons_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(annotation_jsons_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                all_annotations.append(data)

    annotations_df = pl.DataFrame(all_annotations)
    annotations_df = annotations_df.with_columns(pl.col("TEXT_ID").cast(pl.Int64))

    # Reorder annotations_df by TEXTID and PARAGRAPH_ID
    annotations_df = annotations_df.sort(['TEXT_ID'])
    return annotations_df
    