import requests
from bs4 import BeautifulSoup
import re

def fetch_and_parse(url):
    response = requests.get(url)
    response.raise_for_status()                         # raise an error for bad responses
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def extract_content(soup) -> str:
    content = soup.find('div', {'id': 'textcontainer'})

    if not content:
        content = soup.body                             # default if no specific div is found

    text = content.get_text(separator='\n', strip=True)
    return text

def clean_text(text) -> str:
    text = re.sub(r'\s+', ' ', text)                    #  whitespace
    text = re.sub(r'[^A-Za-z0-9.,;:?!\s]', '', text)    #  unwanted characters
    return text.strip()

if __name__ == "__main__":
    urls = 
    [
        "https://bulletins.psu.edu/undergraduate/colleges/abington/#majorsminorsandcertificatestext",
        "https://bulletins.psu.edu/undergraduate/general-information/academic-information/undergraduate-degrees-requirements/"
    ]

    parsed_data = [fetch_and_parse(url) for url in urls]
    content_list = [extract_content(soup) for soup in parsed_data]

    cleaned_content = [clean_text(content) for content in content_list]

    # Display the cleaned content
    for content in cleaned_content:
        print(f"[content] {content}\n\n\n")
