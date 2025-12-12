# python3 -m pip install requests beautifulsoup4

import requests
from bs4 import BeautifulSoup
import re

def extract_dates(date_str):
    date_raw_components = date_str.split(' ')
    date_str = date_raw_components[0]
    date_notes = ' '.join(date_raw_components[1:])
    went1 = False
    went2 = False
    if date_str[-1] in ('–', '-'):
        date_str = date_str[:-1]
        went1 = True
    if date_str[-1] == '*':
        date_str = date_str[:-1]
        went2 = True
    # Pattern matches "MM/DD-MM/DD" or "MM/DD"
    try:
        match = re.match(r'^(\d{1,2}/\d{1,2})(?:-(\d{1,2}/\d{1,2}))?$', date_str)
        if not match:
            raise ValueError("Input string is not a valid date or date range format")
    except:
        print(went1, went2)
        print("problem:", '||'+date_str+'||')
        raise
    first = match.group(1)
    last = match.group(2) if match.group(2) else first
    # Find exclusions
    exclusions = []
    if "Closed" in date_notes:
        exclusions = re.findall(r'\b\d{1,2}/\d{1,2}\b', date_notes)
    return first, last, exclusions

def scrape_ohio_festivals():
    url = "https://ohiofestivals.net/ohio-festivals/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/121.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    # soup = BeautifulSoup(response.text, "html.parser")
    # print(soup.prettify())
    # print('...........')
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Traverse for the desired article element
    article = soup.find("article")
    if not article:
        raise Exception("No <article> found")

    # Inside that, div.inside-article
    inside_article = article.find("div", class_="inside-article")
    if not inside_article:
        raise Exception("No <div class='inside-article'> found")

    # Inside that, div.entry-content
    entry_content = inside_article.find("div", class_="entry-content")
    if not entry_content:
        raise Exception("No <div class='entry-content'> found")

    # Walk through all <p> elements
    found_transition = False
    all_contents = []
    for p in entry_content.find_all("p"):
        p_text = p.get_text(strip=True)
        if not found_transition:
            if "Looking for festivals in other states?" in p_text:
                found_transition = True
            continue
        # After finding the transition paragraph, start parsing
        if not p.find("a"):
            continue  # skip paragraphs without <a>
        # Break at <br>
        chunks = []
        # Use the descendants to split chunks at <br> - preserves tags
        chunk = []
        for elem in p.contents:
            if elem == '\n':
                continue
            if str(elem).startswith("<br"):
                if chunk:
                    chunks.append(chunk)
                chunk = []
            else:
                chunk.append(elem)
        if chunk:
            chunks.append(chunk)
        # Now process each chunk
        for chunk_elems in chunks:
            has_a = False
            for ce in chunk_elems:
                if isinstance(ce, str):
                    continue
                if ce.name == "a":
                    has_a = True
                    break
            if not has_a:
                continue
            # Find all elements in order: pre-text, <a>, post-text
            pre_text = ""
            link_href = ""
            link_text = ""
            post_text = ""
            i = 0
            n = len(chunk_elems)
            # Find first a tag
            for ix, ce in enumerate(chunk_elems):
                if getattr(ce, 'name', None) == "a":
                    # Everything before is pre_text
                    pre_parts = [
                        x
                        for x in chunk_elems[:ix]
                        if isinstance(x, str)
                    ]
                    pre_text = " ".join([pt.strip() for pt in pre_parts]).strip()
                    link_href = ce.get("href", "")
                    link_text = ce.get_text(strip=True)
                    # Everything after is post_text
                    post_parts = [
                        x
                        for x in chunk_elems[ix+1:]
                        if isinstance(x, str)
                    ]
                    post_text = " ".join([pt.strip() for pt in post_parts]).strip()
                    all_contents.append([pre_text, link_href, link_text, post_text])
                    break  # we only want the first a per chunk

    # Format output
    """
    IN: [date_str, URL, event_name, city] <= poorly formatted strings
    OUT: {
        "dates": [list_of_dates], 
        "URL": URL, 
        "event": event_name", 
        "city": city, 
        #"county": county
    }
    """
    all_events = []
    for line in all_contents:
        # Extract raw data
        date_raw = line[0]
        URL = line[1]
        event_name = line[2]
        city_raw = line[3]
        # Cleanup city, remove event if discontinued
        if 'DISCONTINUED' in city_raw:
            continue
        city_stripped = ("".join(ch for ch in city_raw if ch.isalpha())).lower()
        # Convert date
        first_date, last_date, exclusions = extract_dates(date_raw)
        all_events.append({
            "dates": [first_date, last_date, '!', *exclusions],
            "URL": URL,
            "event": event_name,
            "city": city_stripped,
            #"county": None
        })
        print('||'+city_stripped+'||')

    return all_events

if __name__ == "__main__":
    data = scrape_ohio_festivals()
    # for entry in data:
    #     print(entry)