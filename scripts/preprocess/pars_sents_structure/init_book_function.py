import importlib
import sys
import os

script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))
sys.path.append(script_dir)
from setup import Book

path_to_modules = "scripts/preprocess/pars_sents_structure/book_functions/"

with open(path_to_modules+"/A_TEMPLATE.py","r") as f:
    template = f.read()


books = Book.fetch_all_books()
for b in books:
    module_name = f"split.book_functions.{b.folder_name}"

    try:
        module = importlib.import_module(module_name)
        print(f"The module for {b} already exists in book_functions/.\n")

    except ImportError:
        # create file to fill in, following template
        with open(f"{path_to_modules}/{b.folder_name}.py","w") as f:
            f.write(template)
