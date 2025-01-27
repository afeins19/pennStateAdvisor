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

def clean_text_for_major(major_data_dict):
    """Cleans keys and values in a dictionary by removing HTML artifacts and extra spaces."""
    illegal_patterns = {r"\xa0": " ", r"\s+": " "}  # Non-breaking spaces and extra spaces
    
    cleaned_dict = {}

    for k, v in major_data_dict.items():
       
        # clean values -> only clean strings since some might be lists or something else
        if isinstance(v, str):  
            new_value = v
            for pattern, replacement in illegal_patterns.items():
                new_value = re.sub(pattern, replacement, new_value)
        else:
            new_value = v  

        cleaned_dict[k] = new_value

    return cleaned_dict


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
                    "course_url": major_url,
                })

            if "c or better" in course_code.lower():
                needs_c_or_better = True

    return course_list

def extract_additional_courses(major_url):
    response = requests.get(major_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    course_list = []

    needs_c_or_better = False 
    found_additional_section = False
    # find all courses in the prescribed section
    for row in soup.select(".sc_courselist tr.odd, .sc_courselist tr.even"):
        columns = row.find_all("td")

        if len(columns) >= 2:        
            
            course_code = columns[0].get_text(strip=True)
            course_name = columns[1].get_text(strip=True)
            credits = columns[-1].get_text(strip=True)  # credits is last col

            if "select" in course_code.lower():
                break


            # exit conditions
            if "requirements for" in course_code.lower():
                break


            if "supporting" in course_code.lower():
                break 
            
    
            if r"&" in str(course_code.lower()[:1]): 
                course_code = str(course_code)[:1] # drop the & 

            # dropping header from table for prescribed c or better 
            if "additional" not in course_code.lower() and found_additional_section:
                course_list.append({
                    "course_code": course_code,
                    "course_name": course_name,
                    "credits": credits,
                    "needs_c_or_better" : needs_c_or_better,
                    "course_url": major_url,
                    "equivalent_course" : "",
                })


            elif "additional" in course_code.lower():
                found_additional_section = True

            if "c or better" in course_code.lower():
                needs_c_or_better = True

            # line starts with 'or' so we have to consider the prev course
            if "orclass" in row.get("class", []):
                or_removed = str(course_code).split("or",1)[1].strip()
                course_list[-1]['course_code'] = or_removed # drop the or 
                course_list[-1]['equivalent_course'] = course_list[-2]['course_code'] # make the prev course iterated over the equivalent one
                course_list[-2]['equivalent_course'] = or_removed # make prev eq course 
                

    return course_list

def extract_selectable_courses(major_url):
    """Groups courses under their 'Select n from...' headers and extracts required credits."""
    response = requests.get(major_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    course_groups = []
    current_group = None  

    for row in soup.find_all("tr"):  # Loop through table rows to capture both headers and courses
        columns = row.find_all("td")

        if len(columns) == 2:  # Selection header row (e.g., "Select one of the following")
            header_text = columns[0].get_text(strip=True).lower()
            required_credits = columns[1].get_text(strip=True)  # Credits in second column

            if "select" in header_text:  # New selection group detected
                if current_group:
                    course_groups.append(current_group)  # Save the previous group
                
                current_group = {
                    "selection_requirement": header_text,
                    "required_credits": required_credits,
                    "courses": []
                }

        elif current_group and len(columns) >= 2:  # Course row under a selection header
            course_code = columns[0].get_text(strip=True)
            course_name = columns[1].get_text(strip=True)

            # Extract course URL if available
            course_link = columns[0].find("a", class_="bubblelink code")
            course_url = urljoin(BASE_URL, course_link["href"]) if course_link else "N/A"

            current_group["courses"].append({
                "course_code": course_code,
                "course_name": course_name,
                "course_url": course_url
            })

    # Add the last group if it's not empty (end of table)
    if current_group:
        course_groups.append(current_group)

    return course_groups

    
def extract_course_comments(major_url):
    comments = []
    response = requests.get(major_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # comments are right below <tr class="even/odd lastrow>"
    lastrow_trs = soup.find_all("tr", class_=lambda c: c and "lastrow" in c)
    
    comment_spans = soup.find_all("span", class_="courselistcomment")

    for c in comment_spans:
        text = c.get_text(strip=True)
        
        if any(keyword in text.lower() for keyword in ["prescribed courses", "additional courses", "supporting courses", "bachelor of science", "requirements", "option"]):
                continue  # Skip section headers

        elif "select" in text.lower() and "following" not in text.lower():
            print(f"\nCOMMENT >>> {text}")
            comments.append(text)
            
    return comments 

def extract_credit_breakdown(major_url):
    """Extracts the credit breakdown (Gen Ed, Electives, Major Req, etc.) from the degree requirements section."""
    response = requests.get(major_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    credit_breakdown = {}

    # Find all tables, some majors list credit breakdown separately
    credit_tables = soup.find_all("table", class_="sc_sctable tbl_programrequirements")  

    for table in credit_tables:
        for row in table.find_all("tr"):
            cols = row.find_all("td")

            if len(cols) >= 2:  # Ensures row has at least Category & Credit columns
                category = cols[0].get_text(strip=True)
                credits = cols[1].get_text(strip=True)

                # Skip rows that don't have valid credit numbers
                if not re.search(r"\d+", credits):  
                    continue  

                # Normalize category names to avoid inconsistencies
                category = category.replace("\xa0", " ").strip()

                # Store the credit breakdown
                credit_breakdown[category] = credits

    return credit_breakdown

def extract_major_options(major_url):
    """gets course requirements for majors with options (in tg12 tag)."""
    options = []
    
    response = requests.get(major_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Locate the dropdown div that holds options (if it exists)
    option_div = soup.find("div", id="tg12")
    if not option_div:
        return []  #  empty if no options exist

    # get all option titles -> h5 tags 
    option_titles = option_div.find_all("h5")

    for option_title in option_titles:
        option_text = option_title.get_text(strip=True)  # full text
        match = re.match(r"(.+?)\s*\((\d+)\s*credits?\)", option_text)  # name & credits

        if match:
            option_name = match.group(1).strip()
            option_credits = match.group(2).strip()
        else:
            option_name = option_text  # fallback if regex fails
            option_credits = "N/A"

        # find the corresponding course table
        option_table = option_title.find_next("table", class_="sc_courselist")

        option_courses = []

        if option_table:
            rows = option_table.find_all("tr")

            for row in rows:
                columns = row.find_all("td")

                if len(columns) >= 3:  # format (Code, Name, Credits)
                    course_code = columns[0].get_text(strip=True)
                    course_name = columns[1].get_text(strip=True)
                    credits = columns[2].get_text(strip=True)

                    if "select one of" in course_code.lower():
                        break

                    # Extract course URL if available
                    course_link = columns[0].find("a", class_="bubblelink code")
                    course_url = urljoin(BASE_URL, course_link["href"]) if course_link else "N/A"

                    option_courses.append({
                        "course_code": course_code,
                        "course_name": course_name,
                        "credits": credits,
                        "course_url": course_url
                    })

        # store option data
        options.append({
            "option_name": option_name,
            "option_credits": option_credits,
            "courses": option_courses
        })

    return options


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
    

    cleaned_prescribed_courses = list(map(clean_text_for_major, prescribed_courses))
    cleaned_additional_courses = list(map(clean_text_for_major, additional_courses))

    comment = extract_course_comments(major_url)

    # get options for courses (additional specializations) 
    course_options = None 
    selectable_courses = extract_selectable_courses(major_url)

    print(f"\n\t[Getting Data] {major_title} | {major_code}\n")
 


    major_data = {
        "major_title" : major_title,
        "major_code" : major_code,
        "min_credit_info" : min_credit_info,
        "credit_breakdown" : credit_breakdown,
        "prescribed_courses" : prescribed_courses,
        "additional_courses" : additional_courses,
        "selectable_courses" : selectable_courses,
        "comments" : comment,
        "options" : course_options
    }

    for k,v in major_data.items():
        if isinstance(v, str):
            print(f"{k}: {v}")
        else:
            if v is not None:
                print(f"{k}: {len(v)} items")
            
    return major_data

if __name__ == "__main__":
	links=get_baccalaureate_degree_links()

	for link in links:
		major_data = generate_major_requirements(link)
