# python3 -m pip install requests beautifulsoup4

import requests
from bs4 import BeautifulSoup

def scrape_ohio_festivals():
    url = "https://ohiofestivals.net/ohio-festivals/"
    response = requests.get(url)
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

    return all_contents

if __name__ == "__main__":
    data = scrape_ohio_festivals()
    for entry in data:
        print(entry)