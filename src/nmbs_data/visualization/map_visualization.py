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
    planning_dir = paths['planning_dir']  # Use lowercase key
    
    if gtfs_file is None:
        # Find first GTFS file in planning directory
        for file in os.listdir(planning_dir):
            if file.endswith('.zip') and 'GTFS' in file:
                gtfs_file = os.path.join(planning_dir, file)
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
    Load train station data with coordinates and additional details like name and platform.
    
    Args:
        file_path: Path to the station data file or GTFS file (optional if using API)
        
    Returns:
        dict: Dictionary mapping station IDs to details including coordinates, name and platform
    """
    station_data = {}
    
    # First try to use the API
    try:
        stops_df = api_client.get_stops_df()
        if len(stops_df) > 0:
            print(f"Using API for station data: {len(stops_df)} stations")
            
            # Try different column name variations
            lat_cols = ['stop_lat', 'latitude', 'lat', 'y', 'stop_latitude']
            lon_cols = ['stop_lon', 'longitude', 'lon', 'x', 'stop_longitude']
            id_cols = ['stop_id', 'station_id', 'id', 'code']
            name_cols = ['stop_name', 'name', 'station_name']
            platform_cols = ['platform_code', 'platform', 'platformCode']
            
            found_lat = next((col for col in lat_cols if col in stops_df.columns), None)
            found_lon = next((col for col in lon_cols if col in stops_df.columns), None)
            found_id = next((col for col in id_cols if col in stops_df.columns), None)
            found_name = next((col for col in name_cols if col in stops_df.columns), None)
            found_platform = next((col for col in platform_cols if col in stops_df.columns), None)
            
            if found_lat and found_lon and found_id:
                for _, row in stops_df.iterrows():
                    station_id = str(row[found_id])
                    lat = row[found_lat]
                    lon = row[found_lon]
                    
                    # Get station name if available
                    station_name = ""
                    if found_name and pd.notna(row[found_name]):
                        station_name = row[found_name]
                        
                    # Get platform number if available
                    platform = ""
                    if found_platform and pd.notna(row[found_platform]):
                        platform = row[found_platform]
                        
                    if pd.notna(lat) and pd.notna(lon):
                        station_data[station_id] = {
                            'coords': [lat, lon],
                            'name': station_name,
                            'platform': platform
                        }
                
                print(f"Loaded {len(station_data)} station details from API")
                return station_data
    except Exception as e:
        print(f"Error loading station data from API: {e}")
    
    # If API fails, fallback to local file with basic information
    if not file_path:
        paths = get_data_paths()
        planning_dir = paths['planning_dir']
        
        # Try to extract from GTFS file
        stops_df, _, _, _ = extract_gtfs_data(file_path)
        if stops_df is not None and 'stop_lat' in stops_df.columns and 'stop_lon' in stops_df.columns:
            for _, row in stops_df.iterrows():
                station_id = str(row['stop_id'])
                lat = row['stop_lat']
                lon = row['stop_lon']
                
                # Try to get station name if available
                station_name = ""
                if 'stop_name' in stops_df.columns and pd.notna(row['stop_name']):
                    station_name = row['stop_name']
                    
                # Try to get platform if available
                platform = ""
                if 'platform_code' in stops_df.columns and pd.notna(row['platform_code']):
                    platform = row['platform_code']
                
                if pd.notna(lat) and pd.notna(lon):
                    station_data[station_id] = {
                        'coords': [lat, lon],
                        'name': station_name,
                        'platform': platform
                    }
            
            print(f"Loaded {len(station_data)} station details from GTFS file")
            return station_data
        
        # Try other potential files
        potential_files = [
            os.path.join(planning_dir, "stations.csv"),
            os.path.join(planning_dir, "stations.json")
        ]
        for path in potential_files:
            if os.path.exists(path):
                file_path = path
                break
    
    # If no station data found, use some default Belgian stations
    if not station_data:
        print("No station data found. Using default Belgian station coordinates.")
        station_data = {
            "8814001": {
                'coords': [50.8358, 4.3353],
                'name': "Bruxelles-Midi/Brussel-Zuid",
                'platform': ""
            },
            "8821006": {
                'coords': [51.2172, 4.4212],
                'name': "Antwerpen-Centraal",
                'platform': ""
            },
            "8891009": {
                'coords': [51.0352, 3.7094],
                'name': "Gent-Sint-Pieters",
                'platform': ""
            },
            "8844008": {
                'coords': [50.6404, 5.5715],
                'name': "Liège-Guillemins",
                'platform': ""
            },
            "8892007": {
                'coords': [51.2060, 3.2161],
                'name': "Bruges",
                'platform': ""
            },
            "8841004": {
                'coords': [50.6326, 5.5651],
                'name': "Namur",
                'platform': ""
            },
            "8863008": {
                'coords': [50.4591, 3.9561],
                'name': "Mons",
                'platform': ""
            },
            "8844305": {
                'coords': [50.4238, 4.4700],
                'name': "Charleroi-Sud",
                'platform': ""
            }
        }
    
    return station_data

def get_route_color(route_index, total_routes, route_type=None):
    """Generate a color for a route based on its index and type."""
    # Use different hue ranges based on route type
    if route_type is not None:
        # Map route types to different hue ranges
        type_hue_ranges = {
            0: (0.0, 0.1),    # Tram
            1: (0.1, 0.2),    # Subway/Metro
            2: (0.2, 0.5),    # Rail
            3: (0.5, 0.7),    # Bus
            4: (0.7, 0.8),    # Ferry
            5: (0.8, 0.9),    # Cable car
            6: (0.9, 1.0)     # Gondola/Suspended cable car
        }
        
        # Default to rail if type not in mapping
        hue_range = type_hue_ranges.get(route_type, (0.2, 0.5))
        
        # Calculate hue within the type's range
        hue = hue_range[0] + (route_index / max(1, total_routes)) * (hue_range[1] - hue_range[0])
    else:
        # Distribute hues evenly across the spectrum if no type info
        hue = route_index / max(1, total_routes)
    
    # Create a vibrant RGB color
    r, g, b = [int(255 * c) for c in colorsys.hsv_to_rgb(hue, 0.8, 0.9)]
    return f'#{r:02x}{g:02x}{b:02x}'

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
    routes = []
    
    try:
        # Verify we have required columns
        required_trip_cols = ['trip_id', 'route_id', 'service_id']
        required_stop_time_cols = ['trip_id', 'stop_id', 'stop_sequence']
        required_route_cols = ['route_id', 'route_type']
        
        # Check if required columns exist in dataframes
        if not all(col in trips_df.columns for col in required_trip_cols):
            print(f"Warning: Missing required columns in trips_df. Available: {trips_df.columns.tolist()}")
            return routes
            
        if not all(col in stop_times_df.columns for col in required_stop_time_cols):
            print(f"Warning: Missing required columns in stop_times_df. Available: {stop_times_df.columns.tolist()}")
            return routes
            
        if not all(col in routes_df.columns for col in required_route_cols):
            print(f"Warning: Missing required columns in routes_df. Available: {routes_df.columns.tolist()}")
            return routes
        
        # Sample a subset of trips to reduce complexity (max 100 routes)
        route_ids = routes_df['route_id'].unique()
        route_sample = route_ids[:min(100, len(route_ids))]
        
        # Process each route
        for route_id in route_sample:
            # Get trips for this route
            route_trips = trips_df[trips_df['route_id'] == route_id]
            
            # If no trips found, continue to next route
            if len(route_trips) == 0:
                continue
                
            # Get route type
            route_type = routes_df[routes_df['route_id'] == route_id]['route_type'].iloc[0]
            if isinstance(route_type, str) and route_type.isdigit():
                route_type = int(route_type)
            elif not isinstance(route_type, (int, float)):
                route_type = 2  # Default to rail
                
            # Take the first trip as representative of the route
            sample_trip_id = route_trips['trip_id'].iloc[0]
            
            # Get stop times for this trip
            trip_stops = stop_times_df[stop_times_df['trip_id'] == sample_trip_id]
            
            # Sort by stop sequence
            if 'stop_sequence' in trip_stops.columns:
                trip_stops = trip_stops.sort_values('stop_sequence')
            
            # Extract the stop IDs in sequence
            stop_ids = trip_stops['stop_id'].astype(str).tolist()
            
            # Only include routes with at least 2 stops
            if len(stop_ids) >= 2:
                # Get trip headsign if available
                trip_headsign = ''
                if 'trip_headsign' in route_trips.columns:
                    trip_headsign = route_trips['trip_headsign'].iloc[0]
                
                # Get route short name if available
                route_name = f"Route {route_id}"
                if 'route_short_name' in routes_df.columns:
                    route_name_val = routes_df[routes_df['route_id'] == route_id]['route_short_name'].iloc[0]
                    if pd.notna(route_name_val) and str(route_name_val).strip():
                        route_name = str(route_name_val)
                
                # Create the route object
                route = {
                    "train_id": f"{route_name} ({sample_trip_id})",
                    "route_type": route_type,
                    "stations": stop_ids,
                    "route_id": route_id,
                    "headsign": trip_headsign
                }
                routes.append(route)
        
        print(f"Constructed {len(routes)} routes from GTFS data")
        
    except Exception as e:
        print(f"Error constructing routes from GTFS: {e}")
    
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
    # Determine center of map based on stations
    if station_coords:
        coords = list(station_coords.values())
        avg_lat = sum(coord[0] for coord in coords) / len(coords)
        avg_lon = sum(coord[1] for coord in coords) / len(coords)
    else:
        # Default to center of Belgium if no stations
        avg_lat, avg_lon = 50.8503, 4.3517
    
    # Create a map centered on average coordinates
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=7, 
                  tiles='CartoDB dark_matter' if dark_mode else 'OpenStreetMap')
    
    # Create a feature group for all stations
    station_group = folium.FeatureGroup(name="All Stations")
    
    # Create a marker cluster for stations
    station_cluster = MarkerCluster(name="Station Clusters")
    station_group.add_child(station_cluster)
    
    # Add stations to the map
    for station_id, coords in station_coords.items():
        # Create a marker for the station
        popup_text = f"Station ID: {station_id}"
        folium.CircleMarker(
            location=coords,
            radius=3,
            popup=popup_text,
            fill=True,
            fill_opacity=0.7,
            color='white' if dark_mode else 'blue',
            fill_color='white' if dark_mode else 'blue'
        ).add_to(station_cluster)
    
    # Add station group to map
    m.add_child(station_group)
    
    # Create a feature group for routes
    routes_group = folium.FeatureGroup(name="Train Routes")
    
    # Add routes to the map
    for i, route in enumerate(routes):
        # Extract route data
        stations = route.get('stations', [])
        route_type = route.get('route_type', 2)  # Default to rail
        train_id = route.get('train_id', f"Route {i}")
        headsign = route.get('headsign', '')
        
        # Generate a color for the route
        color = get_route_color(i, len(routes), route_type)
        
        # Collect coordinates for all stations in the route
        route_coords = []
        for station_id in stations:
            if station_id in station_coords:
                route_coords.append(station_coords[station_id])
        
        # Only create route if we have at least 2 stations with coords
        if len(route_coords) >= 2:
            # Create a polyline for the route
            route_name = f"{train_id}"
            if headsign:
                route_name += f" to {headsign}"
                
            folium.PolyLine(
                locations=route_coords,
                color=color,
                weight=3,
                opacity=0.7,
                popup=route_name
            ).add_to(routes_group)
    
    # Add routes group to map
    m.add_child(routes_group)
    
    # Add real-time data if available
    if realtime_data:
        realtime_group = folium.FeatureGroup(name="Real-time Positions")
        
        # Process vehicle positions if available
        if "vehicle_positions" in realtime_data:
            for position in realtime_data["vehicle_positions"]:
                if "lat" in position and "lon" in position:
                    # Create a marker for the vehicle
                    vehicle_id = position.get("vehicle_id", "Unknown")
                    trip_id = position.get("trip_id", "Unknown")
                    
                    popup_text = f"Vehicle: {vehicle_id}<br>Trip: {trip_id}"
                    folium.Marker(
                        location=[position["lat"], position["lon"]],
                        popup=popup_text,
                        icon=folium.Icon(color='red', icon='bus')
                    ).add_to(realtime_group)
        
        # Process API real-time data if available
        if "api_realtime" in realtime_data:
            api_data = realtime_data["api_realtime"]
            if "entity" in api_data:
                for entity in api_data["entity"]:
                    # Extract vehicle position data if available
                    if "vehicle" in entity and "position" in entity["vehicle"]:
                        position = entity["vehicle"]["position"]
                        if "latitude" in position and "longitude" in position:
                            # Create a marker for the vehicle
                            vehicle_id = entity["vehicle"].get("vehicle", {}).get("id", "Unknown")
                            trip_id = entity["vehicle"].get("trip", {}).get("tripId", "Unknown")
                            
                            popup_text = f"Vehicle: {vehicle_id}<br>Trip: {trip_id}"
                            folium.Marker(
                                location=[position["latitude"], position["longitude"]],
                                popup=popup_text,
                                icon=folium.Icon(color='red', icon='bus')
                            ).add_to(realtime_group)
        
        # Add real-time group to map
        m.add_child(realtime_group)
    
    # Add layer control to toggle visibility
    folium.LayerControl().add_to(m)
    
    # Save the map if output_path is provided
    if output_path:
        m.save(output_path)
    
    return m

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
    # Use planning_dir instead of PLANNING_DIR to match the updated structure
    planning_dir = paths['planning_dir']
    
    # Try to construct routes from GTFS
    stops_df, routes_df, trips_df, stop_times_df = extract_gtfs_data(file_path)
    
    if all(df is not None for df in [trips_df, stop_times_df]):
        routes = construct_routes_from_gtfs(trips_df, stop_times_df, routes_df)
        if routes:
            return routes
    
    routes = []
    
    # If not GTFS or GTFS processing failed, try other formats
    if file_path is None:
        file_path = os.path.join(planning_dir, "routes.csv")
    
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
    maps_dir = paths['MAPS_DIR']  # Use uppercase key to match what's returned by ensure_directories()
    
    # Ensure directories exist
    ensure_directories()
    
    # Set default output file if not provided
    if output_file is None:
        output_file = "train_routes_map.html"
    output_path = os.path.join(maps_dir, output_file)
    
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