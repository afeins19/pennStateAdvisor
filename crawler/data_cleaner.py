# Preprocessing CSV file
#   - converting to lowercase
#   - stop word removal
#   - punctuation removal

import pandas as pd
import numpy as np
import csv
import nltk
import ast
import string
from nltk.corpus import stopwords as sw
from nltk.tokenize import word_tokenize as wt

nltk.download("stopwords")
nltk.download("punkt_tab")


def clean_txt(txt: str) -> str:
    stop_words = set(sw.words("english"))
    punc_table = str.maketrans("", "", string.punctuation)

    txt = txt.lower()  # lowercase
    txt = txt.translate(punc_table)  # drop punctuation
    words = wt(txt)  # tokenization
    words = [w for w in words if w not in stop_words]  # stopword removal
    return "".join(words)


with open("psu_courses.csv", mode="r") as inf, open(
    "processed_psu_courses.csv", mode="w"
) as outf:
    reader = csv.DictReader(inf)
    field_names = reader.fieldnames
    print(field_names)

    writer = csv.DictWriter(outf, fieldnames=field_names)
    writer.writeheader()

    # processing description
    for record in reader:
        if "description" in record:
            record["description"] = clean_txt(record["description"])

        # convert string of form "['a','b','c']" -> ['a', 'b', 'c']
        if "learning_objectives" in record:
            record["learning_objectives"] = ast.literal_eval(
                record["learning_objectives"]
            )

        writer.writerow(record)
