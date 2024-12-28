import streamlit as st
import googlemaps
import folium
from streamlit_folium import folium_static
import pandas as pd
import re

# ============================
# Streamlit Application
# ============================

def main():
    st.set_page_config(page_title="📍 Google Places Nearby Addresses Visualization", layout="wide")
    st.title("📍 Google Places Nearby Addresses Visualization")
    st.markdown("""
    This application allows you to input an address and visualize it along with nearby addresses from Google Places on an interactive map.
    """)
    
    # ============================
    # Sidebar - User Inputs
    # ============================
    st.sidebar.header("🔑 API Configuration")
    
    # Input: Google Maps API Key
    api_key = st.sidebar.text_input("Enter your Google Maps API Key:", type="password")
    
    # Validate API Key presence
    if not api_key:
        st.sidebar.warning("Please enter your Google Maps API key to proceed.")
        st.stop()
    
    # Initialize Google Maps client
    try:
        gmaps_client = googlemaps.Client(key=api_key)
        # Test the API key by making a simple request
        gmaps_client.geocode("Test")
    except Exception as e:
        st.sidebar.error(f"Invalid API Key or connection error: {e}")
        st.stop()
    
    st.sidebar.header("📍 Address Search Parameters")
    
    # Input: Address
    address_input = st.sidebar.text_input("Enter Address:", "Παπαφλέσσα 145, Αθήνα, 18546")
    
    # Input: Search Radius
    radius_input = st.sidebar.slider("Search Radius (meters):", min_value=100, max_value=2000, value=500, step=100)
    
    # Button to generate map
    if st.sidebar.button("🔍 Generate Map"):
        # Geocode the address
        with st.spinner("📡 Geocoding the address..."):
            main_coords = geocode_address(address_input, gmaps_client)
        
        if not main_coords:
            st.error("❌ Geocoding failed: Address not found.")
            st.stop()
        
        lat, lon = main_coords
        st.success(f"✅ Coordinates: Latitude = {lat}, Longitude = {lon}")
        
        # Extract postcode for more accurate querying
        postcode = extract_postcode(address_input)
        
        # Fetch nearby places using Google Places API
        with st.spinner("🔄 Fetching nearby addresses from Google Places..."):
            nearby_addresses = fetch_nearby_places(gmaps_client, main_coords, radius_input)
        
        if not nearby_addresses:
            st.error("❌ No nearby addresses found.")
            st.stop()
        
        st.success(f"✅ Found {len(nearby_addresses)} nearby addresses.")
        
        # Generate Folium map
        with st.spinner("🗺️ Generating the map..."):
            folium_map = generate_folium_map_google_places(address_input, main_coords, nearby_addresses, radius=radius_input)
        
        # Display the map
        st.subheader("🗺️ Map Visualization")
        folium_static(folium_map, width=700, height=500)
        
        # Optional: Display the list of nearby addresses
        if st.checkbox("📋 Show Nearby Addresses"):
            st.subheader("📌 Nearby Addresses")
            st.write(pd.DataFrame(nearby_addresses, columns=["Nearby Addresses"]))
    
# ============================
# Helper Functions
# ============================

def geocode_address(address, gmaps_client):
    """
    Geocodes the given address using Google Maps Geocoding API and returns latitude and longitude.
    """
    try:
        geocode_result = gmaps_client.geocode(address, language='el', components={"country": "GR"})
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return (location['lat'], location['lng'])
        else:
            return None
    except Exception as e:
        st.error(f"Geocoding error: {e}")
        return None

def extract_postcode(address):
    """
    Extracts the postcode from the address string.
    Assumes the postcode is the last numeric component in the address.
    """
    match = re.search(r'\b\d{4,5}\b', address)
    if match:
        return match.group()
    return None

def fetch_nearby_places(gmaps_client, location, radius=500):
    """
    Fetches nearby addresses using Google Places API's Nearby Search.
    """
    try:
        response = gmaps_client.places_nearby(
            location=location,
            radius=radius,
            type='street_address'
        )
        results = response.get('results', [])
        
        # Extract formatted addresses
        addresses = [place.get('vicinity', '') for place in results]
        # Remove duplicates
        unique_addresses = list(dict.fromkeys(addresses))
        return unique_addresses
    except Exception as e:
        st.error(f"Error fetching nearby places: {e}")
        return []

def generate_folium_map_google_places(main_address, main_coords, nearby_addresses, radius=500):
    """
    Generates a Folium map with the main address and nearby addresses fetched from Google Places.
    """
    lat, lon = main_coords
    
    # Initialize the Folium map centered at the main address
    try:
        m = folium.Map(
            location=main_coords,
            zoom_start=17,
            tiles='Stamen Toner',
            attr='Map tiles by Stamen Design, under CC BY 3.0. Data by Google Places.'
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
    
    # Add a circle to represent the search radius
    folium.Circle(
        radius=radius,
        location=main_coords,
        popup='Search Radius',
        color='blue',
        fill=False
    ).add_to(m)
    
    # Add a marker cluster for nearby addresses
    marker_cluster = folium.plugins.MarkerCluster().add_to(m)
    
    # Add nearby addresses markers (Blue)
    for address in nearby_addresses:
        # Geocode each nearby address to get coordinates
        coords = geocode_address(address, gmaps_client=gmaps_client)
        if coords:
            folium.Marker(
                location=coords,
                popup=address,
                icon=folium.Icon(color='blue', icon='home')
            ).add_to(marker_cluster)
    
    return m

# ============================
# Run the Application
# ============================

if __name__ == "__main__":
    main()
