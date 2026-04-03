import folium
import time

import helpers as hf
import scrape_ohio_festivals as sof


def plot_city_list(ohio_cities, date):

	# Center the map on Ohio
	ohio_center = [40.3675, -82.9962]
	my_map = folium.Map(location=ohio_center, zoom_start=7)

	# Get coordinates for each city
	sidebar_content = ''
	num_cities = 0
	num_done   = 0
	num_big_cities = 0
	sidebar_rows = []
	for row in ohio_cities:
		city   = row['city']
		event  = row['event']
		url    = row['URL']
		county = row['county']
		coords = row['coords']
		is_done = row['is_done']
		is_big  = row['is_big']
		if coords:
			# Add points for each city
			color = "green" if is_done else ("red" if is_big else "blue")
			folium.Marker(
				coords, 
				popup=city, 
				icon=folium.Icon(color=color)
			).add_to(my_map)
			link = f'<a href="{url}">{event}</a>'
			sidebar_row_data = f'<b>{city}</b>: {link}<br><i>{county} county</i>'
			strk1 = '<del>' if is_done else ''
			strk2 = '</del>' if is_done else ''
			sidebar_rows.append(f'<li>{strk1}{sidebar_row_data}{strk2}</li>')
			num_cities += 1
			if is_big:
				num_big_cities += 1
			if is_done:
				num_done += 1
		else:
			print(f"Could not geocode city: {city}")
	# Add the sidebar
	sidebar_rows = sorted(sidebar_rows)
	sidebar_content = (
		f'<h2>{date} - {num_big_cities}({num_cities}) Events, {num_done} Repeats </h2><ul>' + \
		''.join(sidebar_rows) + '</ul>'
	)
	sidebar_wrapped = f'''
		<div style="position: fixed; top: 50px; left: 50px; max-height: 500px; overflow-y: auto;
		background-color: white; border:2px solid grey; z-index: 900; padding: 10px;">
		{sidebar_content}
		</div>
	'''
	my_map.get_root().html.add_child(folium.Element(sidebar_wrapped)) #(my_map, sidebar_content, position='left')

	# Save the map to an HTML file
	my_map.save("../_DATA_/tmp_output/ohio_cities_map.html")
	print("Map saved to ohio_cities_map.html")
	print("  Open it at file:///C:/Users/brahm/repos/evang_planner/_DATA_/tmp_output/ohio_cities_map.html")
	print("Legend:")
	print("  Red:   TODO city")
	print("    Dark red: TODO city with no events all summer")
	print("  Green: DONE city (or village)")
	print("  Blue:  TODO village")


if __name__ == "__main__":
	desired_date = input('Enter desired date:  ')
	desired_prox = input('near or far or both: ')
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
	for row in fests:
		if not row['unhandled_city']:
			if desired_date in row['dates']:
				city = row['city']
				county = row['county']
				event = row['event']
				is_wanted = False
				is_done = False
				is_big = False
				coords = None
				if county in close_counties:
					if (desired_prox in ['near', 'both']):
						is_wanted = True
						listings = sof.close_listings
				else:
					if (desired_prox in ['far', 'both']):
						is_wanted = True
						listings = sof.far_listings
				if is_wanted:
					is_done = sof.determine_status(county, city, listings, 'is_done')
					is_big  = sof.determine_status(county, city, listings, 'is_big')
					coords  = sof.determine_status(county, city, listings, 'coords', None)
					new_row = {**row, 'is_done': is_done, 'is_big': is_big, 'coords': coords}
					printable.append([city, event])
					full_rows.append(new_row)
	print('---------------------------------')
	hf.print_cols(printable, ' => ')
	plot_city_list(full_rows, desired_date)
