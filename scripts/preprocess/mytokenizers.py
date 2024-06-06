from tqdm import tqdm
import polars as pl
import spacy
import re

from setup import get_language

lang = get_language()
if lang == "Dutch":
    spacymodel = "nl_core_news_sm"
else:
    spacymodel = "en_core_web_sm"
try:
    nlp = spacy.load(spacymodel)
except OSError:
    spacy.cli.download(spacymodel)
    nlp = spacy.load(spacymodel)



def w_pbar(pbar, func):
    def foo(*args, **kwargs):
        pbar.update(1)
        return func(*args, **kwargs)

    return foo


def tok_sentences(text):
    """
    Splits text into setences
    Returns string where sents are separated by newline
    """
    doc = nlp(text)
    sents = [sent.text for sent in doc.sents if re.search("[A-Za-z0-9]+",sent.text)]
    return sents


def tok_sentences_df(df):
    """
    Return list of sentences and sentence count
    """
    num_lines = df.select(pl.col("paragraphs")).height

    with tqdm(total=num_lines) as pbar:
        # Apply sentence tokenization and join sentences with newline
        df_with_sents = df.with_columns(
            pl.col("paragraphs").map_elements(w_pbar(pbar, tok_sentences), return_dtype=pl.List(pl.Utf8)).alias("sentences")
        )

    # Flatten the list of sentences
    df_with_sents = df_with_sents.with_columns(
        pl.col("sentences").map_elements("\n".join, return_dtype=pl.Utf8).alias("sentences")
    )
    
    return df_with_sents