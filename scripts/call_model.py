import polars as pl
import instructor
import llama_cpp
import sys
import os
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from setup import model_and_pars

modelfile, _, _, _,_,_,_ = model_and_pars()

def load_model():
    """
    You can customize thsi based on your model
    """
    print(f"Loading: {modelfile}")
    llama = llama_cpp.Llama(
        model_path=modelfile,
        n_gpu_layers=-1,
        chat_format="llama-3", 
        n_ctx=2048,
        logits_all=True,
        verbose=False,
        echo = False,
        temperature=0
    )  

    create = instructor.patch(
        create=llama.create_chat_completion_openai_v1,
        mode=instructor.Mode.JSON_SCHEMA,
    )

    return create


def retrieve_missing_data(outfolder, txts_df, pars_df, col):
    """
    Filters texts that do not have 
    corresponding JSON in outfolder
    on which the model has to run.

    col is the column corresponding to the data processed by the 
    LLM (e.g., sentences, clauses)
    """

    existing_files = [re.search("\d+",f.split('.')[0]).group() for f in os.listdir(outfolder) if f.endswith('.json')]
    txts_df = txts_df.with_columns(
        pl.col(col)
        .cast(pl.Utf8)
        )
    missing_txts = txts_df.filter(
        ~pl.col(col)
        .is_in(existing_files)
        )
    
    # Filter paragraphs corresponding to the missing texts
    missing_paragraph_ids = missing_txts.select("paragraph_id").unique()
    missing_paragraphs = pars_df.filter(
        pl.col("paragraph_id")
        .is_in(missing_paragraph_ids.to_series())
        )
    
    return missing_txts, missing_paragraphs