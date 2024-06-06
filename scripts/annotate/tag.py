"""
Takes the books divided into sentences
and finds the clauses in each sentence
"""
from pydantic import BaseModel, Field, field_validator
from aggregate_annotations import annotations_to_tsv
from typing import Literal
from datetime import datetime

from tqdm import tqdm
import polars as pl
import json
import sys
import os

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--retry', action='store_true', help='Triggers the model to only run on sentences that were unsuccessfully split.')
parser.add_argument('--sentences', action='store_true', help='Triggers the model to annotate the sentences of the book.')
parser.add_argument('--clauses', action='store_true', help='Triggers the model to annotate the clauses of the book.')
args = parser.parse_args()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from in_out_manager import tsv_to_df, create_outfolder, save_df_to_tsv
from setup import Book, get_language, model_and_pars
from call_model import load_model, retrieve_missing_data

book = Book.fetch_book()
lang=get_language()
_, _, tag_sys_prompt, _, instruction, _, mydescription = model_and_pars()




class NarrativeLabel(BaseModel):
    chosen_label: Literal["S", "E", "C"]= Field(
        description=mydescription
    )
    @field_validator('chosen_label')
    def check_exists(cls, v):
        if not v:
            return "ERROR IN LABELING OUTPUT"
        if v not in ["S", "E", "C"]:
            return "ERROR IN LABELING OUTPUT"
        return v

def annotate(input_text,input_par,create,labeling_prompt):
    """
    For an input text, determines if it is
    a subjective experience, event, or contextual information
    """
    if lang=="Dutch":
        content= f"{instruction} Hier is de contextparagraaf: {input_par} ## Label dit gedeelte: {input_text}"
    else:
        content=f"{instruction} Here is the context paragraph: {input_par} ## Please label this portion: {input_text}"
    extraction = create(
        response_model=NarrativeLabel,
            messages=[
            {
            "role": "system",
            "content": f"{labeling_prompt}",
            },
            {
            "role": "user",
            "content": content,
            }
            ]
        )

    label =  extraction.model_dump()["chosen_label"]

    return label


def create_input_paragraph(matching_rows, column, max_sentences=10):
    """
    If paragraph is too long, split it
    """
    input_paragraphs = []

    # Get unique sentence IDs
    unique_sentence_ids = matching_rows.select("sentence_id").unique().to_series().sort()
    if len(unique_sentence_ids) > max_sentences:
        # Split into blocks of max_sentences different sentence_ids
        for start in range(0, len(unique_sentence_ids), max_sentences):
            end = start + max_sentences
            block_sentence_ids = unique_sentence_ids[start:end].to_list()
            block_rows = matching_rows.filter(pl.col("sentence_id").is_in(block_sentence_ids))
            
            input_par = ""
            for mrow in block_rows.iter_rows(named=True):
                rowtext = mrow[column]  
                inid = mrow[column[:-1] + "_id"]
                input_par += f"{inid}. {rowtext} "
            
            input_paragraphs.append(input_par.strip())
    else:
        input_par = ""
        for mrow in matching_rows.iter_rows(named=True):
            rowtext = mrow[column]  
            inid = mrow[column[:-1] + "_id"]  
            input_par += f"{inid}. {rowtext} "
        
        input_paragraphs.append(input_par.strip())
    
    return input_paragraphs


def save_errors(errorfile,textid,intext,label):
    with open(errorfile, "a") as error_file:
        error_file.write(f"Text ID: {textid}\n")
        error_file.write(f"Original text: {intext}\n")
        error_file.write(f"Found label: {label}\n\n")

def label_texts(create,text_df,pars_df,labeling_prompt,outfolder,column):
    """
    Loop for annotation
    """
    num_texts = text_df.height
    print("Labeling the book. This can take some time.")

    with tqdm(total=num_texts, position=0, leave=True) as pbar_total:
        for row in pars_df.iter_rows(named=True):
            paragraph_id = row["paragraph_id"]
            chpt_id = row["chapter_id"]
            
            matching_rows = text_df.filter(pl.col("paragraph_id") == paragraph_id)
            input_pars = create_input_paragraph(matching_rows,column)
            
            for mrow in matching_rows.iter_rows(named=True):
                intext = mrow[column]
                inid = mrow[column[:-1]+"_id"]
                intext = f"{inid}. {intext}"
                inpar = [x for x in input_pars if intext in x]
                if len(inpar)!=1:
                    sys.exit("Error in how paragraph {paragraph_id} was reconstructed.")
                else:
                    ipr = inpar[0]
                    label = annotate(intext,ipr,create,labeling_prompt)
                pbar_total.update(1)

                # check for mistakes
                if  label!="ERROR IN LABELING OUTPUT":
                    outfilename = f"{outfolder}/Text{inid}.json"
                    outdict = {
                        "CHAPTER_ID":chpt_id,
                        "TEXT_ID":inid,
                        "PARAGRAPH_ID":paragraph_id,
                        "TEXT":mrow[column],
                        "LABEL":label.strip()
                               }
                    with open(outfilename, "w") as output_file:
                        json.dump(outdict, output_file)
                else:
                    save_errors(errorfile,inid[0],mrow[column],label)


if __name__=="__main__":
    create = load_model()
    
    errorfile = f"{book.folder_path}/labeling_errors.txt"
    with open(errorfile, "w") as myf:
        myf.write(f"RUN {datetime.now()}\n")

    pars_df = tsv_to_df(book.paragraph_filename)

    if args.sentences:
        text_df = tsv_to_df(book.sentence_filename)
        column = "sentences"
    else:
        text_df = tsv_to_df(book.clause_filename)
        column = "clauses"
    outfolder = f"{book.annotation_folder}/{column}/"
    original_input_df = text_df
    if args.retry:
        text_df, pars_df = retrieve_missing_data(outfolder,text_df,pars_df,column[:-1]+"_id")
    else:
        create_outfolder(outfolder)
    label_texts(create,text_df,pars_df,tag_sys_prompt,outfolder,column)
    original_input_len = text_df.height
    text_df, pars_df = retrieve_missing_data(outfolder,text_df,pars_df, "sentence_id")
    if text_df.height!=0:
        print(f" \u2717 {text_df.height} out of {original_input_len} input texts were not annotated.")
        print(f"Go check the issues in {errorfile}.")
        if column=="clauses":
            col=""
        else:
            col=f"-- {column}"
        print(f"To solve the issue, please run $python3 scripts/annotate/tag.py {col} --retry")
    else:
        print(f" \u2713 All annotations successfully saved.")
        os.remove(errorfile)
        ann_df = annotations_to_tsv(book, column)
        outfile_ann = f"{book.folder_path}/corpus_{column}.tsv"
        save_df_to_tsv(outfile_ann,ann_df)
        print(f" \u2713 Corpus saved in {outfile_ann}.")

