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

# Get paths from data_paths module
def get_data_paths():
    """Get standard data paths using data_paths module"""
    paths = ensure_directories()
    return {
        'DATA_DIR': paths['data_dir'],
        'PLANNING_DIR': paths['planning_dir'],
        'MAPS_DIR': paths['maps_dir']
    }

def extract_gtfs_data(gtfs_file=None):
    """
    Extract station and route data from GTFS files.
    
    Args:
        gtfs_file: Path to the GTFS zip file
        
    Returns:
        tuple: (stations_df, routes_df, trips_df, stop_times_df)
    """
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
    Load station data with coordinates.
    
    Args:
        file_path: Path to the station data file (CSV or JSON)
        
    Returns:
        dict: Dictionary mapping station IDs to coordinates
    """
    paths = get_data_paths()
    PLANNING_DIR = paths['PLANNING_DIR']
    
    station_coords = {}
    
    # Try to get station data from GTFS
    stops_df, _, _, _ = extract_gtfs_data(file_path)
    
    if stops_df is not None and not stops_df.empty:
        # Use GTFS stops.txt data
        if all(col in stops_df.columns for col in ['stop_id', 'stop_lat', 'stop_lon']):
            for _, row in stops_df.iterrows():
                station_coords[row['stop_id']] = (float(row['stop_lat']), float(row['stop_lon']))
            print(f"Loaded {len(station_coords)} stations from GTFS data")
            return station_coords
    
    # If no GTFS data, try loading from other files
    if file_path is None:
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
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
                # Try different column name variations
                lat_cols = ['stop_lat', 'latitude', 'lat', 'y', 'stop_latitude']
                lon_cols = ['stop_lon', 'longitude', 'lon', 'x', 'stop_longitude']
                id_cols = ['stop_id', 'station_id', 'id', 'code']
                
                found_lat = next((col for col in lat_cols if col in df.columns), None)
                found_lon = next((col for col in lon_cols if col in df.columns), None)
                found_id = next((col for col in id_cols if col in df.columns), None)
                
                if found_lat and found_lon and found_id:
                    for _, row in df.iterrows():
                        station_coords[str(row[found_id])] = (float(row[found_lat]), float(row[found_lon]))
            elif file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for station in data:
                        # Try different JSON structures
                        if 'id' in station and 'latitude' in station and 'longitude' in station:
                            station_coords[str(station['id'])] = (float(station['latitude']), float(station['longitude']))
                        elif 'stop_id' in station and 'stop_lat' in station and 'stop_lon' in station:
                            station_coords[str(station['stop_id'])] = (float(station['stop_lat']), float(station['stop_lon']))
    except Exception as e:
        print(f"Error loading station data: {e}")
    
    if not station_coords:
        print("No station coordinates found. Using default Belgian stations.")
        # If no data available, use some example Belgian stations as fallback
        station_coords = {
            "8814001": (50.8366, 4.3353),   # Brussels-South/Midi
            "8821006": (51.2172, 4.4211),   # Antwerpen-Centraal
            "8892007": (50.6407, 5.5720),   # Liège-Guillemins
            "8891009": (51.0356, 3.7105),   # Gent-Sint-Pieters
            "8863008": (50.4092, 4.4449),   # Charleroi-Sud
            "8844008": (51.0384, 4.4819),   # Mechelen
            "8841004": (50.8811, 4.7075)    # Leuven
        }
    
    return station_coords

def get_route_color(route_index, total_routes, route_type=None):
    """
    Generate a distinct color for a route based on its index and type.
    
    Args:
        route_index: Index of the route
        total_routes: Total number of routes
        route_type: Type of route (e.g., train type)
        
    Returns:
        str: Hex color code
    """
    # Base colors for different route types
    route_type_colors = {
        0: "#FF0000",  # Tram - Red
        1: "#0000FF",  # Subway - Blue
        2: "#00AA00",  # Rail - Green
        3: "#FF8800",  # Bus - Orange
        4: "#AA00AA",  # Ferry - Purple
        100: "#006600",  # High-speed rail - Dark green
        101: "#AA0000"   # Intercity - Dark red
    }
    
    # If route type provided and in the map, use that as base
    if route_type is not None and route_type in route_type_colors:
        base_color = route_type_colors[route_type]
        
        # Create a slight variation to distinguish between routes of the same type
        h, s, v = colorsys.rgb_to_hsv(*[int(base_color[i:i+2], 16)/255 for i in (1,3,5)])
        
        # Vary the hue slightly but keep the same general color family
        new_h = (h + (route_index / (total_routes * 5))) % 1.0
        
        # Convert back to RGB and then to hex
        r, g, b = colorsys.hsv_to_rgb(new_h, s, v)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    else:
        # Generate a color from the HSV color space for maximum distinction
        h = route_index / total_routes
        s = 0.8
        v = 0.9
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

def construct_routes_from_gtfs(trips_df, stop_times_df, routes_df):
    """
    Construct routes from GTFS trip and stop_times data.
    
    Args:
        trips_df: DataFrame containing trip data
        stop_times_df: DataFrame containing stop times data
        routes_df: DataFrame containing route data
        
    Returns:
        list: List of routes, each with train_id and sequence of station IDs
    """
    routes = []
    
    if trips_df is None or stop_times_df is None:
        return routes
        
    # Merge route info to get route type
    if routes_df is not None:
        trips_with_route = pd.merge(
            trips_df, 
            routes_df[['route_id', 'route_type', 'route_short_name']], 
            on='route_id',
            how='left'
        )
    else:
        trips_with_route = trips_df
        trips_with_route['route_type'] = 2  # Default to rail
        trips_with_route['route_short_name'] = "Unknown"
    
    # For each trip, get the sequence of stops
    trip_groups = stop_times_df.groupby('trip_id')
    
    # Limit to a reasonable number of trips for performance
    max_trips = 200  # Adjust based on performance and map readability
    trip_ids = list(trips_with_route['trip_id'].unique())[:max_trips]
    
    print(f"Processing {len(trip_ids)} trips (limited from {len(trips_with_route)} for performance)")
    
    for trip_id in trip_ids:
        try:
            # Get trip info including route type
            trip_info = trips_with_route[trips_with_route['trip_id'] == trip_id].iloc[0]
            route_id = trip_info['route_id']
            route_type = trip_info['route_type'] if 'route_type' in trip_info else 2  # Default to rail
            route_name = trip_info['route_short_name'] if 'route_short_name' in trip_info else "Unknown"
            
            # Get stop sequence for this trip
            if trip_id in trip_groups.groups:
                trip_stops = trip_groups.get_group(trip_id).sort_values('stop_sequence')
                
                # Build route
                stations = trip_stops['stop_id'].tolist()
                
                if len(stations) > 1:  # Only include routes with multiple stops
                    routes.append({
                        'train_id': f"{route_name}_{trip_id[-4:]}",
                        'route_id': route_id,
                        'route_type': route_type,
                        'stations': stations
                    })
        except Exception as e:
            print(f"Error processing trip {trip_id}: {e}")
    
    print(f"Successfully constructed {len(routes)} routes")
    return routes

def load_route_data(file_path=None):
    """
    Load train route data.
    
    Args:
        file_path: Path to the route data file or GTFS file
        
    Returns:
        list: List of routes, each containing a sequence of station IDs
    """
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
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
                # Process according to your data format
                # This is just an example structure, adjust to your actual data
                for train_id, group in df.groupby('train_id'):
                    stations = group['station_id'].tolist()
                    routes.append({
                        'train_id': train_id,
                        'stations': stations
                    })
            elif file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Parse JSON structure (adjust according to your data)
                    for route in data:
                        routes.append(route)
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
    # Choose map tiles based on mode
    if dark_mode:
        tiles = "CartoDB dark_matter"
    else:
        tiles = "cartodbpositron"
    
    # Initialize map centered on Belgium
    m = folium.Map(
        location=[50.8503, 4.3517],  # Brussels
        zoom_start=8,
        tiles=tiles
    )
    
    # Add station markers
    stations_group = folium.FeatureGroup(name="All Stations")
    marker_cluster = MarkerCluster().add_to(stations_group)
    
    for station_id, coords in station_coords.items():
        folium.Marker(
            location=coords,
            popup=f"Station ID: {station_id}",
            icon=folium.Icon(color="blue", icon="train", prefix="fa")
        ).add_to(marker_cluster)
    
    stations_group.add_to(m)
    
    # Create route type groups
    route_types = {}
    for route in routes:
        route_type = route.get('route_type', 2)  # Default to rail (2) if not specified
        if route_type not in route_types:
            label = {
                0: "Trams",
                1: "Subway",
                2: "Rail",
                3: "Bus",
                4: "Ferry",
                100: "High-speed Rail",
                101: "Intercity"
            }.get(route_type, f"Type {route_type}")
            
            route_types[route_type] = FeatureGroupSubGroup(stations_group, name=label)
            route_types[route_type].add_to(m)
    
    # Add route lines
    for i, route in enumerate(routes):
        route_points = []
        for station_id in route['stations']:
            if station_id in station_coords:
                route_points.append(station_coords[station_id])
        
        if len(route_points) > 1:
            route_type = route.get('route_type', 2)
            color = get_route_color(i, len(routes), route_type)
            
            folium.PolyLine(
                locations=route_points,
                color=color,
                weight=3,
                opacity=0.7,
                popup=f"Train {route['train_id']}"
            ).add_to(route_types.get(route_type, stations_group))
    
    # Add real-time vehicle positions if available
    if realtime_data:
        realtime_group = folium.FeatureGroup(name="Real-time Vehicles")
        
        try:
            # Try to extract vehicle positions using function from the gtfs_realtime_reader module
            if isinstance(realtime_data, dict) and "vehicle_positions" in realtime_data:
                # Already processed positions
                positions = realtime_data["vehicle_positions"]
            else:
                # Process each realtime file
                positions = []
                for data_source, rt_files in realtime_data.items():
                    for filename, data in rt_files.items():
                        if isinstance(data, dict) and "entities" in data:
                            # This looks like GTFS real-time data
                            pos = extract_vehicle_positions({data_source: data})
                            positions.extend(pos)
            
            # Add each vehicle position to the map
            for pos in positions:
                # Create a vehicle marker with rotation
                tooltip = f"Train {pos.get('trip_id', 'Unknown')}"
                popup_html = f"""
                <div>
                    <h4>Train {pos.get('trip_id', 'Unknown')}</h4>
                    <p>Route: {pos.get('route_id', 'Unknown')}</p>
                    <p>Status: {pos.get('status', 'Unknown')}</p>
                    <p>Speed: {pos.get('speed', 'Unknown')} km/h</p>
                    <p>Last update: {pos.get('timestamp', 'Unknown')}</p>
                </div>
                """
                
                # Use different icon colors based on platform change status
                color = "red" if pos.get('has_platform_change', False) else "green"
                
                # Create a vehicle icon that shows direction if bearing is available
                if pos.get('bearing') is not None:
                    icon = folium.features.DivIcon(
                        icon_size=(20, 20),
                        icon_anchor=(10, 10),
                        html=f'''
                        <div style="
                            width: 0; 
                            height: 0; 
                            border-left: 10px solid transparent;
                            border-right: 10px solid transparent;
                            border-bottom: 20px solid {color};
                            transform: rotate({pos.get('bearing', 0)}deg);
                            transform-origin: center;
                        "></div>
                        '''
                    )
                else:
                    icon = folium.Icon(color=color, icon="subway", prefix="fa")
                    
                folium.Marker(
                    location=[pos['latitude'], pos['longitude']],
                    tooltip=tooltip,
                    popup=popup_html,
                    icon=icon
                ).add_to(realtime_group)
            
            realtime_group.add_to(m)
        except Exception as e:
            print(f"Error adding real-time positions to map: {e}")
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add a legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 220px; height: auto;
                background-color: white; border:2px solid grey; z-index:9999; padding: 10px;
                font-size: 14px;">
    <p><strong>Train Route Types</strong></p>
    '''
    
    # Add colored lines for each route type
    for route_type, label in {
        2: "Rail",
        100: "High-speed Rail",
        101: "Intercity",
        0: "Trams",
        1: "Subway"
    }.items():
        color = get_route_color(route_type, 10, route_type)
        legend_html += f'<p><span style="color:{color};"><i class="fa fa-minus"></i></span> {label}</p>'
    
    # Add real-time vehicle indicators to the legend if realtime data was provided
    if realtime_data:
        legend_html += '<p><strong>Real-time Vehicles</strong></p>'
        legend_html += '<p><span style="color:green;"><i class="fa fa-subway"></i></span> On schedule</p>'
        legend_html += '<p><span style="color:red;"><i class="fa fa-subway"></i></span> Delayed/Platform change</p>'
    
    legend_html += '''</div>'''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save map if output path is provided
    if output_path:
        m.save(output_path)
        print(f"Map saved to: {output_path}")
    
    return m

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
    
    # Determine which data source to use
    print("Loading station and route data...")
    
    if gtfs_file and os.path.exists(gtfs_file):
        # Use GTFS file for both stations and routes
        station_coords = load_station_data(gtfs_file)
        routes = load_route_data(gtfs_file)
    else:
        # Try to use separate files
        station_coords = load_station_data(stations_file)
        routes = load_route_data(routes_file)
    
    # Load real-time data if requested
    realtime_data = None
    if include_realtime:
        try:
            # Try to read from the specific bin files using the gtfs_realtime_reader module
            specific_realtime_data = read_specific_realtime_files()
            
            if specific_realtime_data and not any('error' in data for data in specific_realtime_data.values()):
                # Process the data for map visualization
                vehicle_positions = []
                for data_type, data in specific_realtime_data.items():
                    if 'error' not in data:
                        positions = extract_vehicle_positions({data_type: data})
                        vehicle_positions.extend(positions)
                
                if vehicle_positions:
                    print(f"Using {len(vehicle_positions)} vehicle positions from specific real-time files")
                    realtime_data = {"vehicle_positions": vehicle_positions}
            else:
                # If specific file reading failed, fall back to general approach
                print("Falling back to scanning real-time directories")
                realtime_dirs = get_realtime_dirs()
                realtime_data = {}
                
                # Process each directory (simplified to just note the files)
                for i, dir_path in enumerate(realtime_dirs):
                    key = 'with_platform_changes' if i == 0 else 'without_platform_changes'
                    realtime_data[key] = {}
                    
                    for file in os.listdir(dir_path):
                        if file.endswith('.json'):
                            try:
                                with open(os.path.join(dir_path, file), 'r') as f:
                                    realtime_data[key][file] = json.load(f)
                            except Exception as e:
                                print(f"Error loading {file}: {e}")
                
                print(f"Loaded real-time data from {len(realtime_dirs)} directories")
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