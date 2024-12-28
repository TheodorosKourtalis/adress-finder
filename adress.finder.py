import streamlit as st
import overpy
import googlemaps
import folium
from streamlit_folium import folium_static
import json

# ============================
# Configuration and Setup
# ============================

# Replace 'YOUR_GOOGLE_MAPS_API_KEY' with your actual Google Maps API key
GOOGLE_MAPS_API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY'

# Initialize the Google Maps client
gmaps_client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Initialize Overpass API
api = overpy.Overpass()

# ============================
# Helper Functions
# ============================

def geocode_address(address):
    """
    Geocodes the given address using Google Maps Geocoding API and returns latitude and longitude.
    """
    try:
        geocode_result = gmaps_client.geocode(address, language='el')  # 'el' for Greek
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return (location['lat'], location['lng'])
        else:
            st.error("Geocoding failed: Address not found.")
            return None
    except Exception as e:
        st.error(f"Geocoding error: {e}")
        return None

def create_overpass_query(lat, lon, radius=500):
    """
    Creates an Overpass QL query to fetch OSM nodes with address tags within a specified radius around given coordinates.
    """
    query = f"""
    [out:json][timeout:60];
    (
      node(around:{radius},{lat},{lon})["addr:housenumber"]["addr:street"];
    );
    out body;
    """
    return query

def fetch_osm_data(query):
    """
    Fetches OSM data using the Overpass API based on the provided query.
    """
    try:
        result = api.query(query)
        return result
    except overpy.exception.OverpassTooManyRequests:
        st.error("Error: Too many requests to Overpass API. Please try again later.")
    except overpy.exception.OverpassGatewayTimeout:
        st.error("Error: Overpass API gateway timeout. Please try again later.")
    except Exception as e:
        st.error(f"An error occurred while fetching OSM data: {e}")
    return None

def generate_folium_map(main_address, main_coords, nearby_addresses, radius=500):
    """
    Generates a Folium map with the main address and nearby addresses.
    """
    # Initialize the Folium map centered at the main address
    try:
        m = folium.Map(
            location=main_coords,
            zoom_start=17,
            tiles='Stamen Toner',
            attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
        )
    except ValueError as ve:
        st.warning(f"Tile attribution error: {ve}. Switching to 'OpenStreetMap' tiles.")
        m = folium.Map(location=main_coords, zoom_start=17, tiles='OpenStreetMap')

    # Add the main address marker (Red)
    folium.Marker(
        location=main_coords,
        popup=f"<b>Main Address:</b><br>{main_address}",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

    # Add a marker cluster for nearby addresses
    marker_cluster = folium.plugins.MarkerCluster().add_to(m)

    # Add nearby addresses markers (Blue)
    for address in nearby_addresses:
        # Extract address details
        housenumber = address.tags.get('addr:housenumber', '')
        street = address.tags.get('addr:street', '')
        city = address.tags.get('addr:city', '')  # Optional
        postcode = address.tags.get('addr:postcode', '')  # Optional

        # Combine into a display string
        if city and postcode:
            address_display = f"{housenumber} {street}, {city} {postcode}"
        elif city:
            address_display = f"{housenumber} {street}, {city}"
        elif postcode:
            address_display = f"{housenumber} {street}, {postcode}"
        else:
            address_display = f"{housenumber} {street}"

        folium.Marker(
            location=(address.lat, address.lon),
            popup=address_display,
            icon=folium.Icon(color='blue', icon='home')
        ).add_to(marker_cluster)

    # Add a circle to represent the search radius
    folium.Circle(
        radius=radius,
        location=main_coords,
        popup='Search Radius',
        color='blue',
        fill=False
    ).add_to(m)

    return m

# ============================
# Streamlit Application
# ============================

def main():
    st.title("📍 OSM Nearby Addresses Visualization")
    st.markdown("""
    This application allows you to input an address and visualize it along with nearby addresses from OpenStreetMap on an interactive map.
    """)

    # Sidebar for user inputs
    st.sidebar.header("User Input Parameters")

    # Input: Address
    address_input = st.sidebar.text_input("Enter Address:", "Παπαφλέσσα 145, Αθήνα, 18546")

    # Input: Search Radius
    radius_input = st.sidebar.slider("Search Radius (meters):", min_value=100, max_value=2000, value=500, step=100)

    # Button to generate map
    if st.sidebar.button("Generate Map"):
        # Geocode the address
        st.info("Geocoding the address...")
        main_coords = geocode_address(address_input)

        if not main_coords:
            st.stop()

        st.success(f"Coordinates: Latitude = {main_coords[0]}, Longitude = {main_coords[1]}")

        # Create Overpass query
        query = create_overpass_query(main_coords[0], main_coords[1], radius=radius_input)

        # Fetch OSM data
        st.info("Fetching nearby addresses from OpenStreetMap...")
        osm_data = fetch_osm_data(query)

        if not osm_data:
            st.error("No OSM data retrieved.")
            st.stop()

        # Collect nearby addresses
        nearby_addresses = osm_data.nodes
        st.success(f"Found {len(nearby_addresses)} nearby addresses.")

        # Generate Folium map
        st.info("Generating the map...")
        folium_map = generate_folium_map(address_input, main_coords, nearby_addresses, radius=radius_input)

        # Display the map
        st.subheader("Map Visualization")
        folium_static(folium_map)

        # Optional: Display the list of nearby addresses
        if st.checkbox("Show Nearby Addresses"):
            st.subheader("Nearby Addresses")
            address_list = []
            for addr in nearby_addresses:
                housenumber = addr.tags.get('addr:housenumber', '')
                street = addr.tags.get('addr:street', '')
                city = addr.tags.get('addr:city', '')  # Optional
                postcode = addr.tags.get('addr:postcode', '')  # Optional

                # Combine into a display string
                if city and postcode:
                    address_display = f"{housenumber} {street}, {city} {postcode}"
                elif city:
                    address_display = f"{housenumber} {street}, {city}"
                elif postcode:
                    address_display = f"{housenumber} {street}, {postcode}"
                else:
                    address_display = f"{housenumber} {street}"

                address_list.append(address_display)

            st.write(address_list)

# Run the Streamlit app
if __name__ == "__main__":
    main()