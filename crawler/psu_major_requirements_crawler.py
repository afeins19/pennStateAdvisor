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
import requests 
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import re
import pandas as pd
import time 

BASE_URL = f"https://bulletins.psu.edu/undergraduate/colleges/abington/#majorsminorsandcertificatestext"
OUTPUT_FILE_PATH="../csv_files"
OUTPUT_FILE_NAME="psu_major_requirements.csv"


def get_baccalaureate_degree_links():
	response = requests.get(BASE_URL)
	soup = BeautifulSoup(response.content, "html.parser")

	degree_links = [urljoin(BASE_URL, a['href']) for a in soup.select(".sitemap_visual li a")]
	return degree_links

def extract_prescribed_courses(major_url):
    """ the list of prescribed courses """
    response = requests.get(major_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    course_list = []    
    needs_c_or_better = False

    # find all courses in the prescribed section
    for row in soup.select(".sc_courselist tr.odd, .sc_courselist tr.even"):
        columns = row.find_all("td")
        if len(columns) >= 2:
            course_code = columns[0].get_text(strip=True)
            course_name = columns[1].get_text(strip=True)
            credits = columns[-1].get_text(strip=True)  # credits is last col
            
            # accounting only for prescribed courses in this function
            if "additional" in course_code.lower():
                break  
            
            # dropping header from table for prescribed c or better 
            if "Prescribed" not in course_code:
                course_list.append({
                    "course_code": course_code,
                    "course_name": course_name,
                    "credits": credits,
                    "needs_c_or_better" : needs_c_or_better,
                    "course_url": major_url
                })

            if "c or better" in course_code.lower():
                needs_c_or_better = True

    return course_list

def extract_additional_courses(major_url):
    response = requests.get(major_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    course_list = []

    found_additional_section = False
    # find all courses in the prescribed section
    for row in soup.select(".sc_courselist tr.odd, .sc_courselist tr.even"):
        columns = row.find_all("td")
        if len(columns) >= 2:
          
            
            course_code = columns[0].get_text(strip=True)
            course_name = columns[1].get_text(strip=True)
            credits = columns[-1].get_text(strip=True)  # credits is last col
            
            # exit conditions
            if "requirements for" in course_code.lower():
                break

            if "select" in course_code.lower():
                break

            if "supporting" in course_code.lower():
                break 
            
    
            if r"&" in str(course_code.lower()[:1]): 
                course_code = str(course_code)[:1] # drop the & 

            # dropping header from table for prescribed c or better 
            if "additional" not in course_code and found_additional_section:
                course_list.append({
                    "course_code": course_code,
                    "course_name": course_name,
                    "credits": credits,
                    "needs_c_or_better" : needs_c_or_better,
                    "course_url": major_url,
                    "equivalent_course" : ""
                })


            elif "additional" in course_code.lower():
                found_additional_section = True

            if "c or better" in course_code.lower():
                needs_c_or_better = True

            # line starts with 'or' so we have to consider the prev course
            if "or" in str(course_code.lower())[:3]:
                course_code = str(course_code).split("or")[1] # drop the or 
                course_list[-1]['equivalent_course'] = course_list[-2]['course_code'] # make the prev course iterated over the equivalent one
                course_list[-2]['equivalent_course'] = course_code
                

    return course_list
    

def extract_credit_breakdown(major_url):
    # breaking down degree requirments into credit types (gen ed, elective, major requirements etc)
    response = requests.get(major_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    credit_table = soup.find("table", class_="sc_courselist") 
    credit_breakdown = {}

    if credit_table:
        for row in credit_table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 2:
                cat = cols[0].get_text(strip=True)
                credits = cols[1].get_text(strip=True)

                if cat and credits:
                    credit_breakdown[cat] = credits
    
    return credit_breakdown

def generate_major_requirements(major_url):
    response = requests.get(major_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    major_title = soup.find(class_="page-title").get_text(strip=True)
    major_code = soup.find(id="program-code").get_text(strip=True).replace("Program Code: ", "").split("_")[0] 
    min_credit_info = soup.find(class_="areaheader courselistcomment")

    # breaking down degree requirments into credit types (gen ed, elective, major requirements etc)
    credit_breakdown = extract_credit_breakdown(major_url)

    prescribed_courses = extract_prescribed_courses(major_url)
    additional_courses = extract_additional_courses(major_url)

    print(f"[Getting Data] {major_title} | {major_code}\n")
    print(">>> PRESCRIBED COURSES <<<")
    for course in prescribed_courses:
        print(f"\t{course}\n")
    
    print(">>> ADDITIONAL COURSES <<<")
    for course in additional_courses:
        print(f"\t{course}\n")
    time.sleep(5)
    
    time.sleep(5)



    major_data = {
        "major_title" : major_title,
        "major_code" : major_code,
        "min_credit_info" : min_credit_info,
        "credit_breakdown" : credit_breakdown,
        "prescribed_courses" : prescribed_courses,
        "additional_courses" : additional_courses
    }

    return major_data

if __name__ == "__main__":
	links=get_baccalaureate_degree_links()

	for link in links:
		major_data = generate_major_requirements(link)
