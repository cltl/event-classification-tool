"""
Takes the books divided into sentences
and finds the clauses in each sentence
"""
from correct_clauses import apply_correction
from pydantic import BaseModel, Field, field_validator
from typing import List

from tqdm import tqdm
import polars as pl
import string
import json
import sys
import os
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from in_out_manager import save_df_to_tsv
from setup import get_language, model_and_pars

lang=get_language()
_, system_prompt, _, instruction, _, mydescription, _ = model_and_pars()



class ClauseList(BaseModel):

    clauselist:List[str] = Field(
        description=mydescription
    )
    @field_validator('clauselist')
    def replace_empty_list(cls, v):
        if not v:
            return ["ERROR IN SENTENCE SPLITTING OUTPUT"]
        return v


def validate_clauses_match_sentence(clauselist, sentence):
    """
    Checks if original sentence can be reconstructed from the clauses.
    """

    additional_punctuation = '«»'
    all_punctuation = string.punctuation + additional_punctuation

    # Remove all white spaces from the sentence and concatenated clauses
    sentence_no_space_punct = ''.join(c for c in sentence if c not in string.whitespace + all_punctuation)
    joined_clauses_no_space_punct = ''.join(c for c in ''.join(clauselist) if c not in string.whitespace + all_punctuation)

    if sentence_no_space_punct!= joined_clauses_no_space_punct:
        clauselist = apply_correction(clauselist,sentence,lang)
        joined_clauses_no_space_punct = ''.join(c for c in ''.join(clauselist) if c not in string.whitespace + all_punctuation)

    if sentence_no_space_punct != joined_clauses_no_space_punct:
        clauselist = ["ERROR IN SENTENCE SPLITTING OUTPUT"]
    return clauselist


def clausify_sent(sentence,create):
    """
    For a given sentence,
    finds its clauses
    """
    
    extraction = create(
        response_model=ClauseList,
            messages=[
            {
            "role": "system",
            "content": f"{system_prompt}",
            },
            {
            "role": "user",
            "content": f"{instruction} {sentence}",
            }
            ]
        )

    clause_list =  extraction.model_dump()["clauselist"]

    if instruction in clause_list:
        clause_list.remove(instruction)
    if instruction[:-1] in clause_list:
        clause_list.remove(instruction[:-1])

    return clause_list

def save_errors(errorfile,sentid,senttext,clauses):
    with open(errorfile, "a") as error_file:
        error_file.write(f"Sentence ID: {sentid}\n")
        error_file.write(f"Original sentence: {senttext}\n")
        error_file.write(f"Found clauses: {clauses}\n\n")


def find_clauses_in_sents(create,sents_df,pars_df,outfolder,errorfile):
    """
    Loop over sentences to do the splitting
    """
    num_sents = sents_df.height
    print("Splitting the book into clauses. This can take hours.")

    with tqdm(total=num_sents, position=0, leave=True) as pbar_total:
        for row in pars_df.iter_rows(named=True):
            paragraph_id = row["paragraph_id"]
            chapter_id = row["chapter_id"]

            matching_sents = sents_df.filter(pl.col("paragraph_id") == paragraph_id)

            for srow in matching_sents.iter_rows(named=True):
                input_text = srow["sentences"]
                pbar_total.update(1)
                snt_id = srow["sentence_id"]
                
                outdict = { 
                            "CHAPTER_ID":chapter_id,
                            "SENTENCE_ID":snt_id,
                            "PARAGRAPH_ID":srow["paragraph_id"],
                            "SENTENCETEXT":input_text,
                            "CLAUSES":{}
                                }
                
                outfilename = f"{outfolder}/Sentence{snt_id}.json"

                if not re.search("[a-zA-Z]+",input_text):
                    clauses_dict = {0: input_text}
                    outdict["CLAUSES"]=clauses_dict
                    with open(outfilename, "w") as output_file:
                            json.dump(outdict, output_file)
                    continue
                
                clss = clausify_sent(input_text,create)

                # check for mistakes
                out = validate_clauses_match_sentence(clss,input_text)
            
                if "ERROR IN SENTENCE SPLITTING OUTPUT" not in out:
                    clauses_dict = {index: clause for index, clause in enumerate(out)}
                    outdict["CLAUSES"]=clauses_dict
                    with open(outfilename, "w") as output_file:
                        json.dump(outdict, output_file)
                else:
                    save_errors(errorfile,snt_id,input_text,clss)
                    
def aggregate_in_tsv(book):
    clauses_folder = book.clause_folder
    data = []
    
    for filename in os.listdir(clauses_folder):
        if filename.startswith("Sentence") and filename.endswith(".json"):
            with open(os.path.join(clauses_folder, filename), 'r') as file:
                file_data = json.load(file)
                chapter_id = file_data["CHAPTER_ID"]
                paragraph_id = file_data["PARAGRAPH_ID"]
                sentence_id = file_data["SENTENCE_ID"]
                clauses = file_data["CLAUSES"]
                
                for clause_id_in_sentence, clause in clauses.items():
                    data.append({
                        "chapter_id":chapter_id,
                        "paragraph_id": paragraph_id,
                        "sentence_id": sentence_id,
                        "clause_id_in_sentence": int(clause_id_in_sentence),  
                        "clauses": clause
                    })
                

    df = pl.DataFrame(data)
    df = df.with_columns(pl.col("sentence_id").cast(pl.Int64))
    df = df.with_columns(pl.col("clause_id_in_sentence").cast(pl.Int64))
    df = df.sort(by=["paragraph_id","sentence_id", "clause_id_in_sentence"])
    df = df.with_columns(pl.Series("clause_id", range(1, len(df) + 1)))
    
    save_df_to_tsv(book.clause_filename,df)
    print(f" >> Clauses saved in {book.clause_filename}")

