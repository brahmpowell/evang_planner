#import os
import folium
import helpers as hf

def get_coords_for_city(city, city_coords):
    """
    Search for a city's coordinates in the city_coords dictionary.
    Searches across all counties 
    since we don't know the county from the church data.  
    Args:
        city: City name to search for
        city_coords: Nested dictionary of coordinates by county and city
    Returns:
        [latitude, longitude] or None if not found
    """
    for county, cities in city_coords.items():
        if city in cities:
            return cities[city]
    
    return None

def create_church_map(churches_data, city_coords):
    """
    Create a folium map with church markers and popups.
    Combines multiple churches in the same city into a single marker.
    
    Args:
        churches_data: List of dictionaries containing church information
        city_coords: Nested dictionary of coordinates by county and city
    
    Returns:
        folium.Map object
    """
    # Center the map on Ohio
    ohio_center = [40.3675, -82.9962]
    my_map = folium.Map(location=ohio_center, zoom_start=7)
    
    churches_missing_coords = 0
    city_churches = {}  # Dictionary to group churches by city: {city: [church_data, ...]}
    
    # Group churches by city
    for church in churches_data:
        city = church.get('city', '')
        name = church.get('name', '')
        
        if not city or not name:
            print(f"Skipping church with missing city or name: {church}")
            continue
        
        # Get coordinates for this city
        coords = get_coords_for_city(city, city_coords)
        
        if not coords:
            print(f"Could not find coordinates for city: {city}")
            churches_missing_coords += 1
            continue
        
        # Add church to city grouping
        if city not in city_churches:
            city_churches[city] = {'coords': coords, 'churches': []}
        
        city_churches[city]['churches'].append(church)
    
    # Create markers for each city (combining multiple churches if needed)
    churches_plotted = 0
    for city, city_data in city_churches.items():
        coords = city_data['coords']
        churches = city_data['churches']
        
        # Build popup content for all churches in this city
        popup_html = f"<b>{city}</b><br><br>"
        
        for i, church in enumerate(churches):
            name = church.get('name', '')
            
            # Add church name
            popup_html += f"<b>{name}</b><br>"
            
            # Add website if available
            website = church.get('website', '').strip()
            if website:
                # Add http:// if not present
                if not website.startswith('http'):
                    website = 'http://' + website
                popup_html += f'<a href="{website}" target="_blank">{website}</a><br>'
            
            # Add phone if available
            phone = church.get('phone', '').strip()
            if phone:
                popup_html += f"Phone: {phone}<br>"
            
            # # Add separator between churches if not the last one
            # if i < len(churches) - 1:
            #     popup_html += "<hr>"
        
        # Create single marker for this city
        folium.Marker(
            coords,
            popup=folium.Popup(html=popup_html, max_width=300),
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(my_map)
        
        churches_plotted += len(churches)
    
    print(f"Churches plotted: {churches_plotted}")
    if churches_missing_coords > 0:
        print(f"Churches with missing coordinates: {churches_missing_coords}")
    
    return my_map

if __name__ == "__main__":
    """Main function to load churches, create map, and save output."""
    # Load city coordinates
    print("Loading city coordinates...")
    city_coords = hf.read_json('../_DATA_/cities_coords.json')
    
    # Load churches data
    input_file = '../_DATA_/dc_churches.json'
    churches_data = hf.read_json(input_file)
    
    # Create output directory if it doesn't exist
    output_dir = ''
    
    # Create the map
    print(f"Creating church map with {len(churches_data)} churches...")
    my_map = create_church_map(churches_data, city_coords)
    
    # Save the map
    output_file = '../_DATA_/tmp_output/church_map.html'
    my_map.save(output_file)
    
    # Print the file location
    # abs_path = os.path.abspath(output_file)
    # print(f"Map saved to {abs_path}")
    print("  Open it at file:///C:/Users/brahm/repos/evang_planner/_DATA_/tmp_output/church_map.html")