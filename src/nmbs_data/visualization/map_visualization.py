"""
Module for visualizing train routes on a map.
"""

import os
import pandas as pd
import json
import folium
import zipfile
from folium.plugins import MarkerCluster, FeatureGroupSubGroup
import colorsys
# Update imports to use the new package structure
from nmbs_data.data.data_paths import ensure_directories, get_realtime_dirs
from nmbs_data.data.gtfs_realtime_reader import read_specific_realtime_files, extract_vehicle_positions
from nmbs_data.data.api_client import api_client

# Get paths from data_paths module
def get_data_paths():
    """Get standard data paths using data_paths module"""
    paths = ensure_directories()
    return paths

def extract_gtfs_data(gtfs_file=None):
    """
    Extract station and route data from GTFS files or API.
    
    Args:
        gtfs_file: Path to the GTFS zip file (optional if using API)
        
    Returns:
        tuple: (stations_df, routes_df, trips_df, stop_times_df)
    """
    # First try to use the API
    try:
        print("Extracting GTFS data from API...")
        stops_df = api_client.get_stops_df()
        routes_df = api_client.get_routes_df()
        trips_df = api_client.get_trips_df()
        stop_times_df = api_client.get_stop_times_df()
        
        if not all([len(df) > 0 for df in [stops_df, routes_df, trips_df, stop_times_df]]):
            print("Some GTFS data from API was empty, checking for local files...")
        else:
            print(f"Successfully loaded GTFS data from API: {len(stops_df)} stops, {len(routes_df)} routes, {len(trips_df)} trips")
            return stops_df, routes_df, trips_df, stop_times_df
    except Exception as e:
        print(f"Error loading GTFS data from API: {e}")
    
    # If API fails, fallback to local file if provided
    paths = get_data_paths()
    PLANNING_DIR = paths['PLANNING_DIR']
    
    if gtfs_file is None:
        # Find first GTFS file in planning directory
        for file in os.listdir(PLANNING_DIR):
            if file.endswith('.zip') and 'GTFS' in file:
                gtfs_file = os.path.join(PLANNING_DIR, file)
                print(f"Using GTFS file: {gtfs_file}")
                break
    
    if not gtfs_file or not os.path.exists(gtfs_file):
        print("No GTFS file found")
        return None, None, None, None
    
    try:
        # Extract data from GTFS zip file
        with zipfile.ZipFile(gtfs_file, 'r') as zip_ref:
            # Check for required files
            required_files = ['stops.txt', 'routes.txt', 'trips.txt', 'stop_times.txt']
            missing_files = [f for f in required_files if f not in zip_ref.namelist()]
            
            if missing_files:
                print(f"Warning: Missing required GTFS files: {', '.join(missing_files)}")
                return None, None, None, None
            
            # Extract data
            stops_df = pd.read_csv(zip_ref.open('stops.txt'))
            routes_df = pd.read_csv(zip_ref.open('routes.txt'))
            trips_df = pd.read_csv(zip_ref.open('trips.txt'))
            stop_times_df = pd.read_csv(zip_ref.open('stop_times.txt'))
            
            return stops_df, routes_df, trips_df, stop_times_df
    
    except Exception as e:
        print(f"Error extracting GTFS data: {e}")
        return None, None, None, None

def load_station_data(file_path=None):
    """
    Load train station data with coordinates.
    
    Args:
        file_path: Path to the station data file or GTFS file (optional if using API)
        
    Returns:
        dict: Dictionary mapping station IDs to coordinates [lat, lon]
    """
    station_coords = {}
    
    # First try to use the API
    try:
        stops_df = api_client.get_stops_df()
        if len(stops_df) > 0:
            print(f"Using API for station data: {len(stops_df)} stations")
            
            # Try different column name variations
            lat_cols = ['stop_lat', 'latitude', 'lat', 'y', 'stop_latitude']
            lon_cols = ['stop_lon', 'longitude', 'lon', 'x', 'stop_longitude']
            id_cols = ['stop_id', 'station_id', 'id', 'code']
            
            found_lat = next((col for col in lat_cols if col in stops_df.columns), None)
            found_lon = next((col for col in lon_cols if col in stops_df.columns), None)
            found_id = next((col for col in id_cols if col in stops_df.columns), None)
            
            if found_lat and found_lon and found_id:
                for _, row in stops_df.iterrows():
                    station_id = str(row[found_id])
                    lat = row[found_lat]
                    lon = row[found_lon]
                    if pd.notna(lat) and pd.notna(lon):
                        station_coords[station_id] = [lat, lon]
                
                print(f"Loaded {len(station_coords)} station coordinates from API")
                return station_coords
    except Exception as e:
        print(f"Error loading station data from API: {e}")
    
    # If API fails, fallback to local file
    if not file_path:
        paths = get_data_paths()
        PLANNING_DIR = paths['PLANNING_DIR']
        
        # Try to extract from GTFS file
        stops_df, _, _, _ = extract_gtfs_data(file_path)
        if stops_df is not None and 'stop_lat' in stops_df.columns and 'stop_lon' in stops_df.columns:
            for _, row in stops_df.iterrows():
                station_id = str(row['stop_id'])
                lat = row['stop_lat']
                lon = row['stop_lon']
                if pd.notna(lat) and pd.notna(lon):
                    station_coords[station_id] = [lat, lon]
            
            print(f"Loaded {len(station_coords)} station coordinates from GTFS file")
            return station_coords
        
        # Try other potential files
        potential_files = [
            os.path.join(PLANNING_DIR, "stations.csv"),
            os.path.join(PLANNING_DIR, "stations.json")
        ]
        for path in potential_files:
            if os.path.exists(path):
                file_path = path
                break
    
    try:
        # Attempt to load station data based on file extension
        if file_path and os.path.exists(file_path):
            # ... existing code for loading from local file ...
            pass
    except Exception as e:
        print(f"Error loading station data: {e}")
    
    # If no station data found, use some default Belgian stations
    if not station_coords:
        print("No station data found. Using default Belgian station coordinates.")
        station_coords = {
            "8814001": [50.8358, 4.3353],  # Bruxelles-Midi/Brussel-Zuid
            "8821006": [51.2172, 4.4212],  # Antwerpen-Centraal
            "8891009": [51.0352, 3.7094],  # Gent-Sint-Pieters
            "8844008": [50.6404, 5.5715],  # Liège-Guillemins
            "8892007": [51.2060, 3.2161],  # Bruges
            "8841004": [50.6326, 5.5651],  # Namur
            "8863008": [50.4591, 3.9561],  # Mons
            "8844305": [50.4238, 4.4700]   # Charleroi-Sud
        }
    
    return station_coords

def get_route_color(route_index, total_routes, route_type=None):
    """Generate a color for a route based on its index and type."""
    # ... existing code ...

def construct_routes_from_gtfs(trips_df, stop_times_df, routes_df):
    """
    Construct routes from GTFS data.
    
    Args:
        trips_df: DataFrame with trips data
        stop_times_df: DataFrame with stop times data
        routes_df: DataFrame with routes data
        
    Returns:
        list: List of routes, each containing sequence of station IDs
    """
    # ... existing code ...

def load_route_data(file_path=None):
    """
    Load train route data.
    
    Args:
        file_path: Path to the route data file or GTFS file (optional if using API)
        
    Returns:
        list: List of routes, each containing a sequence of station IDs
    """
    # Try to get routes from API first
    try:
        # Get trips, stop times and routes data from API
        trips_df = api_client.get_trips_df()
        stop_times_df = api_client.get_stop_times_df()
        routes_df = api_client.get_routes_df()
        
        if all([len(df) > 0 for df in [trips_df, stop_times_df, routes_df]]):
            routes = construct_routes_from_gtfs(trips_df, stop_times_df, routes_df)
            if routes:
                print(f"Successfully constructed {len(routes)} routes from API data")
                return routes
    except Exception as e:
        print(f"Error constructing routes from API data: {e}")
    
    # If API doesn't work, try to construct routes from local GTFS
    paths = get_data_paths()
    PLANNING_DIR = paths['PLANNING_DIR']
    
    # Try to construct routes from GTFS
    stops_df, routes_df, trips_df, stop_times_df = extract_gtfs_data(file_path)
    
    if all(df is not None for df in [trips_df, stop_times_df]):
        routes = construct_routes_from_gtfs(trips_df, stop_times_df, routes_df)
        if routes:
            return routes
    
    routes = []
    
    # If not GTFS or GTFS processing failed, try other formats
    if file_path is None:
        file_path = os.path.join(PLANNING_DIR, "routes.csv")
    
    try:
        # Attempt to load route data based on file extension
        if os.path.exists(file_path):
            # ... existing code for loading from local file ...
            pass
    except Exception as e:
        print(f"Error loading route data: {e}")
    
    # If no routes found, use example routes
    if not routes:
        print("No routes found. Using example Belgian routes.")
        routes = [
            {"train_id": "IC1234", "route_type": 2, "stations": ["8814001", "8821006", "8891009"]},
            {"train_id": "IC5678", "route_type": 2, "stations": ["8814001", "8892007", "8863008"]},
            {"train_id": "L7890", "route_type": 2, "stations": ["8814001", "8844008", "8841004"]}
        ]
    
    return routes

def create_route_map(routes, station_coords, output_path=None, realtime_data=None, dark_mode=False):
    """
    Create an interactive map showing train routes.
    
    Args:
        routes: List of routes (each containing sequence of station IDs)
        station_coords: Dictionary mapping station IDs to coordinates
        output_path: Path to save the resulting HTML map
        realtime_data: Optional real-time data to show vehicle positions
        dark_mode: Whether to use dark mode theme
    
    Returns:
        folium.Map: The created map object
    """
    # ... existing code ...

def visualize_train_routes(gtfs_file=None, routes_file=None, stations_file=None, output_file=None, include_realtime=True, dark_mode=False):
    """
    Main function to visualize train routes on a map.
    
    Args:
        gtfs_file: Path to the GTFS zip file
        routes_file: Path to the file containing route data
        stations_file: Path to the file containing station data
        output_file: Name of the output HTML file
        include_realtime: Whether to include real-time data in visualization
        dark_mode: Whether to use dark mode theme
        
    Returns:
        str: Path to the generated map file
    """
    # Get paths from data_paths module
    paths = get_data_paths()
    MAPS_DIR = paths['MAPS_DIR']
    
    # Ensure directories exist
    ensure_directories()
    
    # Set default output file if not provided
    if output_file is None:
        output_file = "train_routes_map.html"
    output_path = os.path.join(MAPS_DIR, output_file)
    
    # Load station and route data from API by default
    print("Loading station and route data...")
    station_coords = load_station_data(stations_file)
    routes = load_route_data(routes_file)
    
    # Load real-time data if requested
    realtime_data = None
    if include_realtime:
        try:
            # Get real-time data from API
            print("Loading real-time data from API...")
            api_realtime_data = api_client.get_realtime_data()
            
            if api_realtime_data and 'entity' in api_realtime_data:
                print(f"Using real-time data from API with {len(api_realtime_data['entity'])} entities")
                realtime_data = {"api_realtime": api_realtime_data}
            else:
                print("No real-time data available from API, trying local files...")
                
                # Fall back to local files if API doesn't have data
                specific_realtime_data = read_specific_realtime_files()
                
                if specific_realtime_data and not any('error' in data for data in specific_realtime_data.values()):
                    # Process the data for map visualization
                    vehicle_positions = []
                    for data_type, data in specific_realtime_data.items():
                        if 'error' not in data:
                            positions = extract_vehicle_positions({data_type: data})
                            vehicle_positions.extend(positions)
                    
                    if vehicle_positions:
                        print(f"Using {len(vehicle_positions)} vehicle positions from local files")
                        realtime_data = {"vehicle_positions": vehicle_positions}
        except Exception as e:
            print(f"Error loading real-time data: {e}")
    
    # Create and save map
    print(f"Creating map with {len(routes)} routes and {len(station_coords)} stations...")
    m = create_route_map(routes, station_coords, output_path, realtime_data, dark_mode)
    print(f"Map created and saved to: {output_path}")
    
    return output_path

if __name__ == "__main__":
    # When run directly, generate a map using default settings
    map_path = visualize_train_routes()
    print(f"To view the map, open: {map_path}")