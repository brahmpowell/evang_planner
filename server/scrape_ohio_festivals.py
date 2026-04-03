# python3 -m pip install requests beautifulsoup4

import requests
from bs4 import BeautifulSoup
import time
import re
import calendar
import geopy
from geopy.geocoders import Nominatim

import helpers as hf 

year = 2026

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

def gen_dates(begin, end, exclusions):
    if begin == end:
        dates = [begin]
        return dates
    begin_month, begin_day = begin.split('/')
    end_month,   end_day   = end.split('/')
    if begin_month == end_month:
        days = [x for x in range(int(begin_day), int(end_day)+1)]
        dates = [begin_month+'/'+str(day) for day in days]
    else:
        if int(end_month) - int(begin_month) > 1:
            raise NotImplementedError(
                'Unable to handle non-consecutive months {} and {}'.format(
                    begin_month, end_month
                )
            )
        _, num_days = calendar.monthrange(year, int(begin_month))
        days_1 = [x for x in range(int(begin_day), int(num_days)+1)]
        days_2 = [x for x in range(1,              int(end_day)+1)]
        dates_1 = [begin_month+'/'+str(day) for day in days_1]
        dates_2 = [end_month  +'/'+str(day) for day in days_2]
        dates = dates_1 + dates_2
    dates = [date for date in dates if date not in exclusions]
    return dates

def retrieve_parent_county(city):
    for row in [*close_listings, *far_listings]:
        if row['city'] == city:
            return row['county']
    raise ValueError('Undiscovered city '+city)

geolocator = Nominatim(user_agent="ohio_city_mapper")
def retrieve_coords(city, county, delay=True):
    retry_coords = True
    location = None
    attempts = 1
    while retry_coords:
        try:
            location = geolocator.geocode(f"{city}, {county}, Ohio")
            retry_coords = False
            time.sleep(1)
        except geopy.exc.GeocoderUnavailable:
            rest_time = 5 * min(attempts, 4)
            print(f'Retrying after sleeping {rest_time} sec...')
            time.sleep(rest_time)
            attempts += 1
    if not location:
        coords = None
        print(f"Could not geocode city: {city} ({county})")
    else:
        coords = [location.latitude, location.longitude]
    return coords

def get_city_info():
    orig_cities = hf.read_csv('../_DATA_/original_cities_spreadsheet.csv')
    close_counties = hf.read_json('../_DATA_/close_counties.json')
    cities_coords = hf.read_json('../_DATA_/cities_coords.json', {})
    city_mapping = {}
    close_listings = []
    far_listings = []
    t0 = time.time()
    t00 = time.time()
    for line in orig_cities[3:]:
        # county = hf.strip_string(line[0])
        # city   = hf.strip_string(line[1])
        county = line[0]
        city = line[1]
        if (not city) and (not county):
            continue
        is_big = ('city' in hf.strip_string(line[2])) or (hf.str2int(line[3]) >= 5000)
        is_done = line[4] != ''
        city_mapping[hf.strip_string(city)] = city
        # Check if coords exist
        if county not in cities_coords:
            cities_coords[county] = {}
        if city not in cities_coords[county]:
            cities_coords[county][city] = retrieve_coords(city, county)
        # Collect results
        row = {
            'county': county,
            'city':   city,
            'coords': cities_coords[county][city],
            'is_big': is_big,
            'is_done': is_done
        }
        if county in close_counties:
            close_listings.append(row)
        else:
            far_listings.append(row)
    hf.save_json('../_DATA_/cities_coords.json', cities_coords)
    return city_mapping, close_listings, far_listings
city_mapping, close_listings, far_listings = get_city_info()

def determine_status(county, city, listings, code, default=False):
    assert code in ['is_big', 'is_done', 'coords']
    for row in listings:
        if row['county'] == county:
            if row['city'] == city:
                return row[code]
    return default

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
    city_mapping, close_listings, far_listings = get_city_info()
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
        # Check if city name is unhandled
        try:
            city = city_mapping[city_stripped]
            unhandled_city = False
        except:
            city = city_raw
            unhandled_city = True
        # Convert date
        first_date, last_date, exclusions = extract_dates(date_raw)
        all_events.append({
            "dates": gen_dates(first_date, last_date, exclusions), # [first_date, last_date, '!', *exclusions]
            "URL": URL,
            "event": event_name,
            "city": city,
            "county": retrieve_parent_county(city) if not unhandled_city else None,
            "unhandled_city": unhandled_city
        })

    hf.save_json('../_DATA_/scraped_events.json', all_events)

if __name__ == "__main__":
    scrape_ohio_festivals()
    scrape_ohio_locations()