"""
# scrape

### Requirements for major
- prescribed course (required courses for the major)
- courses where the student needs a C or better 
- for options (like computer science program with data science option)
	- have the general computer science prescribed courses as the necessities 
	- add additional prescribed courses for the option 

### General Eduction 
- scrape general education credit categories 
- save "exploration section" information (gn may be completed with interdomain courses: 3 credits for example)

### University Degree Requirements
- save a list of all University Degree Requirements (first year, cultures, writing across the curriculum)

### raw numbers data
- min gpa 
- min number of credits 
- min credits required to be taken at the school where diploma is earned


- do CSV file saving all the data first
"""

BASE_URL = f"https://bulletins.psu.edu/undergraduate/colleges/abington/#majorsminorsandcertificatestext"
OUTPUT_FILE_PATH="../csv_files"
OUTPUT_FILE_NAME="psu_major_requirements.csv"