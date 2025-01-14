import requests 
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin


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
        prereq_block = block.select_one('.courseblockextra')
        prerequisites = prereq_block.text.strip() if prereq_block else "None"
        
        course_data =  { "Course Number": course_number.strip(),
                        "Course Name": course_name.strip(),
                        "Description": description,
                        "Prerequisites": prerequisites,
                        "department_url": department_url}

        # added course data
        courses.append(course_data)

        for key in course_data.keys():
            print(key, end='\t')
            if course_data[key]:
                print("yup")
            else:
                print("nope")
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


if __name__ == "__main__":
    scrape_psu_courses()