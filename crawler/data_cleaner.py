# Preprocessing CSV file 
#   - converting to lowercase
#   - stop word removal
#   - punctuation removal

import pandas as pd 
import numpy as np 
import csv 

with open('psu_courses.csv') as f:
    reader = csv.DictReader(f)
    field_names = reader.fieldnames
    print(field_names)


    