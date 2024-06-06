import polars as pl
import difflib
import string
import json
import os
import re

def find_missing_char(clause, sentence):
    s = difflib.SequenceMatcher(None, clause, sentence)
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'insert' and (i2 - i1) == 0 and 0 < (j2 - j1) <= 2:
            # Up to two characters are missing in the clause
            return i1, sentence[j1:j2], 'insert'
        elif tag == 'replace' and 0 < (i2 - i1) <= 2 and 0 < (j2 - j1) <= 2:
            # Up to two characters are replaced in the clause
            return i1, sentence[j1:j2], 'replace'
        elif tag == 'delete' and 0 < (i2 - i1) <= 2 and (j2 - j1) == 0:
            # Up to two extra characters in the clause
            return i1, None, 'delete'
    return None, None, None


def apply_correction(clauselist,sentence,lang):
    """
    Checks if the error made by the model is just 
    - a loss of capitalization
    - a loss of a conjunction
    - a loss of a character in a word (e.g. "Yeahh"-->"Yeah")
    - the adding of an initial "politeness" response
    In those cases, makes small adjustment.
    """

    if lang=="Dutch":
        conjunctions = ["en", "maar"] # frequently lost conjunctions
    if lang=="English":
        conjunctions = ["and", "but"]
    for cl in clauselist:
        for c in conjunctions:
            if cl in sentence and c+" "+cl in sentence or c+" "+cl in sentence.lower():
                clauseposit = clauselist.index(cl)
                clauselist[clauseposit]=c+" "+cl
    
        
    # check if the difference is just capitalization
    for cl in clauselist:
        clauseposit = clauselist.index(cl)
        if cl not in sentence and cl.capitalize() in sentence:
            clauselist[clauseposit]=cl.capitalize()
        if cl not in sentence and cl[0].lower()+cl[1:] in sentence:
            clauselist[clauseposit]=cl[0].lower()+cl[1:]


    # Check if some elements are random answers, but the clauses are there
    # and if some mismatch with sentence just by some characters
    corrected_clauses = []
    for clause in clauselist:
        if clause in sentence:
            corrected_clauses.append(clause)
        else:
            while True:
                pos, char, operation = find_missing_char(clause, sentence)
                if pos is not None:
                    if operation == 'insert':
                        try:
                            clause = clause[:pos] + char + clause[pos:]
                        except TypeError:
                            break
                    elif operation == 'replace':
                        try:
                            clause = clause[:pos] + char + clause[pos+1:]
                        except TypeError:
                            break
                    elif operation == 'delete':
                        try:
                            clause = clause[:pos] + clause[pos+1:]
                        except TypeError:
                            break
                else:
                    break
            corrected_clauses.append(clause)
    
    # Final check to ensure clauses are part of the sentence
    final_clauses = []
    for clause in corrected_clauses:
        if clause in sentence:
            final_clauses.append(clause)
    clauselist = final_clauses
    
    return clauselist



def final_check(clausefolderpath,sents_df):
    """
    Checks that output clauses match input sentences
    """
    additional_punctuation = '«»'
    all_punctuation = string.punctuation + additional_punctuation

    for filename in os.listdir(clausefolderpath):
        if filename.endswith('.json') and filename.startswith('Sentence'):
            match = re.search(r'\d+', filename)
            if match:
                sentence_id = int(match.group())

                file_path = os.path.join(clausefolderpath, filename)
                with open(file_path, 'r') as file:
                    json_data = json.load(file)

                json_clause_text = [x for x in json_data['CLAUSES'].values()]
                joined_clauses_no_space_punct = ''.join(c for c in ''.join(json_clause_text) if c not in string.whitespace + all_punctuation)

                # Find the corresponding row in sent_df
                row = sents_df.filter(pl.col('sentence_id') == sentence_id)

                if row.shape[0] > 0:
                    # Get the text from the sentence column
                    df_sentence_text = row[0, 'sentences']
                    sentence_no_space_punct = ''.join(c for c in df_sentence_text if c not in string.whitespace + all_punctuation)

                    if not sentence_no_space_punct == joined_clauses_no_space_punct:
                        print(f"No match found between clause and sentences in {filename}")
                        print(f"Original sentence: {df_sentence_text}")
                        print(f"Clauses {json_clause_text}")
                else:
                    print(f"Clause file {filename} exists but {int(match.group())} is not in the sentence file.")

            else:
                print(f"Clause file for sentence {int(match.group())} not found.")