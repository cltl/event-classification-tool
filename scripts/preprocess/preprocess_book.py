"""
Downloads books (if an url has been specified in books.json)
Splits them into paragraphs, sentences, and clauses
"""
from find_clauses import find_clauses_in_sents, aggregate_in_tsv
from datetime import datetime
import urllib3
import certifi
import shutil
import sys
import os

script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.append(script_dir)

from in_out_manager import save_df_to_tsv, tsv_to_df, create_outfolder
from pars_sents_structure.aggregate_splits import group_paragraphs
from find_pars_sents import preprocess_abook, par_to_sents
from setup import Book
from call_model import load_model, retrieve_missing_data
from correct_clauses import final_check


import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--paragraphs', action='store_true', help='Splits .txt files into paragraphs, saved in .tsv.')
parser.add_argument('--sentences', action='store_true', help='Splits .tsv files where each row is a paragraphs into sentences, saved in .tsv.')
parser.add_argument('--clauses', action='store_true', help='Splits .tsv files where each row is a sentence into clauses, saved in .tsv.')
parser.add_argument('--retry', action='store_true', help='Triggers the model to only find clauses for sentences that were unsuccessfully split.')
args = parser.parse_args()

if args.retry and not args.clauses:
    parser.error("--retry requires --clauses to be specified")


http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
)


def download_book(b):
    response = http.request('GET', b.path)
    text = response.data.decode('utf-8')
    with open(outfilename, "w") as f:
        f.write(text)

    print(f"\n \u2713 {b.title} saved in {outfilename}")


b = Book.fetch_book()
outfilename = b.txt_filename

if not b.path.startswith("./inputs/"):
    download_book(b)

pf = b.paragraph_filename.split("/")[-1]
sf = b.sentence_filename.split("/")[-1]
input_parfile= f"./inputs/{pf}"
input_sentfile= f"./inputs/{sf}"

create_outfolder(b.folder_path)


def dopars():
    if not os.path.isfile(b.txt_filename):
        print(f"\n \u2717 Input file {b.txt_filename} not found.")
        print(f"\n \u2717 If you actually stored your .txt file in `./inputs/`, plese rename it: {b.txt_filename}.")
        sys.exit()
    final_df = preprocess_abook(b)
    par_df = group_paragraphs(final_df)
    save_df_to_tsv(b.paragraph_filename,par_df)
    print(f" >> Book split into paragraphs: {b.folder_path}/{b.folder_name}/.")

def dosents():
    if os.path.isfile(input_parfile):
        shutil.copy(input_parfile,b.paragraph_filename)
    
    
    if not os.path.isfile(b.paragraph_filename):
        print(f"\n \u2717 Input file {input_parfile} not found.")
        print(f"\n \u2717 If you actually stored your .tsv file containing the book paragraphs in `./inputs/`, plese rename it: {b.input_parfile}.")
        sys.exit()
    par_df = tsv_to_df(b.paragraph_filename)
    df_with_sents = par_to_sents(par_df)
    save_df_to_tsv(b.sentence_filename,df_with_sents)
    print(f" >> Book split into sentences: {b.folder_path}/{b.folder_name}/.")


def doclauses():
    if os.path.isfile(input_sentfile):
        shutil.copy(input_sentfile,b.sentence_filename)

    if not os.path.isfile(b.sentence_filename):
        print(f"\n \u2717 Input file {input_sentfile} not found.")
        print(f"\n \u2717 If you actually stored your .txt file containing the book sentences in `./inputs/`, plese rename it: {b.input_sentfile}.")
        sys.exit()
    
    text_df = tsv_to_df(b.sentence_filename)
    if os.path.isfile(b.sentence_filename) and not os.path.isfile(b.paragraph_filename):
        pars_df = text_df
    else:
        pars_df = tsv_to_df(b.paragraph_filename)
    
    create = load_model()
    outfolder = b.clause_folder

    errorfile = f"{b.folder_path}/clause_splitting_errors.txt"
    with open(errorfile, "w") as myf:
        myf.write(f"RUN {datetime.now()}\n")
    
    if args.retry:
        text_df, pars_df = retrieve_missing_data(outfolder,text_df,pars_df, "sentence_id")
    else:
        create_outfolder(outfolder)

    find_clauses_in_sents(create,text_df,pars_df,outfolder,errorfile)
    original_input_len = text_df.height
    text_df, pars_df = retrieve_missing_data(outfolder,text_df,pars_df, "sentence_id")
    if text_df.height!=0:
        print(f" \u2717 {text_df.height} out of {original_input_len} sentences were not split into clauses.")
        print(f"Go check the issues in {errorfile}.")
        print(f"To solve the issue, please run $python3 scripts/preprocess/preprocess_book.py --clauses --retry")
        print(f"or use correct_clauses.ipynb to clausify the missing sentences.")
    else:
        print(f" \u2713 All clauses successfully saved.")
        os.remove(errorfile)
        all_sents_df = tsv_to_df(b.sentence_filename)
        final_check(b.clause_folder,all_sents_df)
        aggregate_in_tsv(b)




if __name__=="__main__":
    if args.paragraphs:
        dopars()
    
    if args.sentences:
        dosents()

    if args.clauses:
        doclauses()