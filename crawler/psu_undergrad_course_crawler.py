import requests 
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import re


# Base URL for the main page
BASE_URL = "https://bulletins.psu.edu/university-course-descriptions/undergraduate/"

# get extract department links
def get_department_links():
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # extract all department links
    links = [urljoin(BASE_URL, a['href']) for a in soup.select('.az_sitemap li a')] # extra parenthese problem
    #links = [BASE_URL + a['href'] for a in soup.select('.az_sitemap li a')]
    return links

# extract courses from a department page
def extract_courses_from_department(department_url):
    response = requests.get(department_url)
    soup = BeautifulSoup(response.content, "html.parser")
    courses = []
    
    # get all course blocks
    course_blocks = soup.select('.courseblock')
    
    for block in course_blocks:
        # get course title 
        title_block = block.select_one('.courseblocktitle') 

        if not title_block:
            print("<<<not a course>>>")
            continue
            

        title_text = title_block.text.strip()
        course_number, course_name = title_text.split(':', 1)
        
        # get description
        description = block.select_one('.courseblockdesc').text.strip() if block.select_one('.courseblockdesc') else "No description"
        
        # get prerequisites
        course_data_block = block.select_one('.courseblockextra')
        course_data = course_data_block.text.strip() if course_data_block else "None"
        
        #print(course_data)
       

        course_data =  { "course_number": course_number.strip(),
                        "course_name": course_name.strip(),
                        "credits" : extract_credits(description),
                        "description": description,
                        "prerequisite_data": extract_prerequisite_data(course_data),
                        "prerequisite_course_numbers": extract_prerequisite_course_numbers(course_data),
                        "equivalent_course_numbers": extract_equivalent_course_numbers(course_data),
                        "learning_objectives": extract_learning_objectives(course_data), # GH, GA, etc.
                        "department_url": department_url}

        # added course data
        courses.append(course_data)
        print(f"Prerequisites: {str(course_data['prerequisite_data'])}")
        print(f"Learning Objectives: {str(course_data['learning_objectives'])}")
        # for key in course_data.keys():
        #     print(key, end='\t')
        #     if course_data[key]:
        #         print("yup")
        #     else:
        #         print("nope")
        print("\n")

        
    return courses

# main function to scrape all courses
def scrape_psu_courses():
    print("Fetching department links...")
    department_links = get_department_links()
    
    all_courses = []
    for link in department_links:
        print(f"Scraping department: {link}")
        department_courses = extract_courses_from_department(link)
        all_courses.extend(department_courses)
    
    # save
    df = pd.DataFrame(all_courses)
    df.to_csv("psu_courses.csv", index=False)
    print("Courses saved to psu_courses.csv")

def extract_prerequisite_data(txt):
    pre_req_start_pattern = "Enforced Prerequisite at Enrollment: "

    pre_reqs = re.split(pre_req_start_pattern, txt)
    if len(pre_reqs) <= 1: 
        return [] 
    return pre_reqs[1:]

def extract_equivalent_course_numbers(txt): 
    # looks for courses under enforced pre-requisite that are like (ABC 123 or DEC 142)
    pattern=f"\sor\s"
    matches = extract_prerequisite_data(txt)
    equivalent_matches = []
    if matches:
        for match in matches:
            equivalent_matches.extend(re.split(pattern, match))
    return equivalent_matches


def extract_prerequisite_course_numbers(txt):
    # if pre-req portion does not in None | Enforced Prerequisite -> None
    # first look for the or case (MATH 123 or Stat 123)

    match_str ="[A-Z]+\s[0-9]+"
    matches = []
    processed_matches=[]
    if txt is not None:
        matches.extend(re.findall(match_str, txt))
        
        for match in matches:
            processed_matches.append(re.sub(f"\\xa0", f" ", match))
            
        # drop \xa0 from matches 
        return processed_matches 
    return [] 


def extract_learning_objectives(txt):
    match_str = f"\([A-Z]+\)"
    matches = []
    if txt is not None:
        matches.extend(re.findall(match_str, txt))
        return matches
    return []

def extract_credits(txt):
    """

    Handles cases like:
    - "3 Credits"
    - "1-12 Credits"
    - "Maximum of 12 Credits"
    - "Introduction to Financial Accounting 1-12 Credits/Maximum of 12"

    """
    # normalize text
    txt = txt.lower().strip()

    range_credit_pattern = r"(\d+)-(\d+)\s+credits?"  #  1-12 Credits
    max_credit_pattern = r"maximum of (\d+)\s+credits?"  #  Maximum of 12 Credits
    single_credit_pattern = r"(\d+)\s+credits?"  #  3 Credits

    
    # cases with a slash ("/") separating values
    if "/" in txt:
        parts = txt.split("/")  # split into two parts
        min_credits, max_credits = None, None

        for part in parts:
            # check for range case
            match = re.search(range_credit_pattern, part)
            if match:
                min_credits, max_credits = int(match.group(1)), int(match.group(2))

            # max case
            match = re.search(max_credit_pattern, part)
            if match:
                max_credits = int(match.group(1))

        if min_credits is not None and max_credits is not None:
            return (min_credits, max_credits)
        elif max_credits is not None:
            return (0, max_credits)  # assume 0 min

    # range case
    match = re.search(range_credit_pattern, txt)
    if match:
        return int(match.group(1)), int(match.group(2))  # (min_credits, max_credits)

    # maximum of case
    match = re.search(max_credit_pattern, txt)
    if match:
        return (0, int(match.group(1)))  # assume min is 0 if none given

    # case single credit values 
    match = re.search(single_credit_pattern, txt)
    if match:
        credits = int(match.group(1))
        return (credits)  # fixed credits are returned 

    return None  # no creditts found

if __name__ == "__main__":
    scrape_psu_courses()