from functools import wraps
import configparser
import os
import re


def read_config():
    """
    Read the config.ini file
    """

    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), "../", "config.ini"))

    title=config.get("book", "title").strip('"')
    path=config.get("book", "path").strip('"')

    language=config.get("language", "lang").strip('"')
    model=config.get("model", "model_path").strip('"')
    
    clause_splitting_system_prompt = config.get("systemprompts", "clause_splitting").strip('"')
    clause_labeling_system_prompt = config.get("systemprompts","labeling").strip('"')
    
    clause_splitting_instruction_prompt = config.get("instructionprompts", "clause_splitting").strip('"')
    clause_labeling_instruction_prompt = config.get("instructionprompts","labeling").strip('"')

    clause_splitting_description = config.get("outputdescriptions", "clause_splitting").strip('"')
    labeling_description = config.get("outputdescriptions","labeling").strip('"')

    
    return title, path, language, model, clause_splitting_system_prompt, clause_labeling_system_prompt, clause_splitting_instruction_prompt, clause_labeling_instruction_prompt, clause_splitting_description, labeling_description


def get_title_path():
    """
    Get the title and path of the book to be processed
    from config.ini
    """

    title = read_config()[0]
    path = read_config()[1]

    return title, path

def get_language():
    lang = read_config()[2]
    return lang


def get_folder_name(title):
    """
    The folder where the downloaded book will be stored
    """

    folder_name = re.sub(r"[^a-zA-Z0-9]+", ' ', title).strip().replace(" ","_").lower()
    
    return folder_name


def model_and_pars():
    """
    Get the model and prompts
    """
    model = read_config()[3]
    split_sys_prompt = read_config()[4]
    label_sys_prompt = read_config()[5]

    split_instr_prompt = read_config()[6]
    label_instr_prompt = read_config()[7]


    split_descr = read_config()[8]
    label_descr = read_config()[9]

    return model, split_sys_prompt, label_sys_prompt, split_instr_prompt, label_instr_prompt, split_descr, label_descr


class Book:
    def __init__(self, title, path):
        # book metadata
        self.title = title
        self.path = path

        # folder where book will be stored
        self.folder_name = get_folder_name(title)
        self.folder_path = os.path.join("outputs/", self.folder_name)
        self.clause_folder = os.path.join(self.folder_path, "clauses")
        self.annotation_folder = os.path.join(self.folder_path,"annotations")
        self.analysis = os.path.join(self.folder_path,"analysis")



        # .txt file of book and .tsv for its paragraphs
        self.txt_filename = f"./inputs/{self.folder_name}.txt"
        self.paragraph_filename = f"{self.folder_path}/{self.folder_name}_paragraphs.tsv"
        self.sentence_filename = f"{self.folder_path}/{self.folder_name}_sentences.tsv"
        self.clause_filename = f"{self.folder_path}/{self.folder_name}_clauses.tsv"

    @classmethod
    def fetch_book(cls):
        title, path = get_title_path()
        return cls(title, path)

    def __repr__(self):
        return f"Book(title='{self.title}',folder='{self.folder_name}', txt='{self.txt_filename}', paragraphs='{self.paragraph_filename}, sentences='{self.sentence_filename}')"
