import time

import helpers as hf
import scrape_ohio_festivals as sof




def is_summer_festival(dates):
	for date in dates:
		month = int(date.split('/')[0])
		if month >= 4:
			if month <= 9:
				return True
	return False

if __name__ == "__main__":
	#desired_date = input('Enter desired date:  ')
	#desired_prox = input('near or far or both: ')
	fests = hf.read_json('../_DATA_/scraped_events.json')
	close_counties = hf.read_json('../_DATA_/close_counties.json')
	# all_events.append({
	#     "dates": [dates...],
	#     "URL": URL,
	#     "event": event_name,
	#     "city": city_stripped,
	#     "county": county,
	#	  "unhandled_city": bool,
	# })
	printable = []
	full_rows = []
	has_fests = {}
	listings = [*sof.close_listings, *sof.far_listings]
	listings = [{**row, 'fests':[]} for row in listings if (row['is_big'] and not row['is_done'])]
	for row in fests:
		if not row['unhandled_city']:
			if is_summer_festival(row['dates']):
				city   = row['city']
				county = row['county']
				event  = row['event']
				is_done = sof.determine_status(county, city, listings, 'is_done')
				is_big  = sof.determine_status(county, city, listings, 'is_big')
				#coords  = sof.determine_status(county, city, listings, 'coords', None)
				if not is_done:
					if is_big:
						# Note it on our list of cities
						for i in range(len(listings)):
							if listings[i]['city'] == city:
								if listings[i]['county'] == county:
									listings[i]['fests'].append(event)
									break
	empties = []
	for row in listings:
		if len(row['fests']) == 0:
			print(row['city'], '({} county)'.format(row['county']))