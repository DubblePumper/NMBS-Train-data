"""
Module for visualizing train routes on a map.
"""

import os
import pandas as pd
import json
import folium
import zipfile
import time
import threading
import datetime
import logging
import requests
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from folium.plugins import MarkerCluster, FeatureGroupSubGroup
import colorsys
from nmbs_data.data.data_paths import ensure_directories, get_realtime_dirs, get_data_filepath
from nmbs_data.data.gtfs_realtime_reader import read_specific_realtime_files, extract_vehicle_positions
from nmbs_data.data.api_client import api_client, get_realtime_data

# Get paths from data_paths module
def get_data_paths():
    """Get standard data paths using data_paths module"""
    paths = ensure_directories()
    return paths

def load_station_data() -> Dict[str, Dict[str, Any]]:
    """
    Load station data from the API.
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of station data with station_id as key
    """
    stations = {}
    
    try:
        # Get stops data from API
        stops_data = api_client.get_stops()
        logging.info(f"Loaded {len(stops_data)} stops from API")
        
        # Process stops data
        for stop in stops_data:
            stop_id = stop.get('stop_id')
            if not stop_id:
                continue
                
            # Get coordinates if available
            stop_lat = stop.get('stop_lat')
            stop_lon = stop.get('stop_lon')
            
            # Skip stops without valid coordinates
            if not stop_lat or not stop_lon:
                continue
                
            try:
                lat = float(stop_lat)
                lon = float(stop_lon)
                
                # Skip stops with invalid coordinates
                if lat == 0 and lon == 0:
                    continue
                    
                stations[stop_id] = {
                    'name': stop.get('stop_name', f'Station {stop_id}'),
                    'coords': (lat, lon),
                    'zone_id': stop.get('zone_id'),
                    'location_type': stop.get('location_type'),
                    'parent_station': stop.get('parent_station'),
                }
            except (ValueError, TypeError):
                logging.warning(f"Invalid coordinates for station {stop_id}")
    
    except Exception as e:
        logging.error(f"Error loading station data: {e}")
        # Fallback to empty stations dictionary will be handled by the caller
    
    return stations

def load_trips_data() -> Dict[str, Dict[str, Any]]:
    """
    Load trips data from the API.
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of trip data with trip_id as key
    """
    trips = {}
    
    try:
        # Get trips data from API
        trips_data = api_client.get_trips()
        logging.info(f"Loaded {len(trips_data)} trips from API")
        
        # Process trips data
        for trip in trips_data:
            trip_id = trip.get('trip_id')
            if not trip_id:
                continue
                
            trips[trip_id] = {
                'route_id': trip.get('route_id'),
                'service_id': trip.get('service_id'),
                'trip_headsign': trip.get('trip_headsign', ''),
                'trip_short_name': trip.get('trip_short_name', ''),
                'direction_id': trip.get('direction_id'),
                'block_id': trip.get('block_id'),
                'shape_id': trip.get('shape_id'),
                'stops': []  # Will be populated with stop_times data
            }
    except Exception as e:
        logging.error(f"Error loading trips data: {e}")
    
    return trips

def load_stop_times_data(trips_dict: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Load stop times data from the API and populate trips with their stops.
    
    Args:
        trips_dict (Dict[str, Dict[str, Any]]): Dictionary of trip data to populate
        
    Returns:
        Dict[str, Dict[str, Any]]: Updated dictionary of trip data with stops
    """
    try:
        # Get stop_times data from API
        stop_times_data = api_client.get_stop_times()
        logging.info(f"Loaded {len(stop_times_data)} stop times from API")
        
        # Process stop_times data and add to trips
        for stop_time in stop_times_data:
            trip_id = stop_time.get('trip_id')
            if not trip_id or trip_id not in trips_dict:
                continue
                
            stop_id = stop_time.get('stop_id')
            if not stop_id:
                continue
                
            stop_sequence = int(stop_time.get('stop_sequence', 0))
            
            # Add stop to trip's stops list
            trips_dict[trip_id]['stops'].append({
                'stop_id': stop_id,
                'stop_sequence': stop_sequence,
                'arrival_time': stop_time.get('arrival_time'),
                'departure_time': stop_time.get('departure_time'),
                'pickup_type': stop_time.get('pickup_type'),
                'drop_off_type': stop_time.get('drop_off_type')
            })
        
        # Sort each trip's stops by stop_sequence
        for trip_id, trip_data in trips_dict.items():
            trip_data['stops'] = sorted(trip_data['stops'], key=lambda x: x['stop_sequence'])
    
    except Exception as e:
        logging.error(f"Error loading stop times data: {e}")
    
    return trips_dict

def load_route_data() -> List[Dict[str, Any]]:
    """
    Load route data from the API.
    
    Returns:
        List[Dict[str, Any]]: List of route data
    """
    routes = []
    
    try:
        # Get routes data from API
        routes_data = api_client.get_routes()
        logging.info(f"Loaded {len(routes_data)} routes from API")
        
        # Process routes data
        for route in routes_data:
            route_id = route.get('route_id')
            if not route_id:
                continue
            
            # Create a route object
            route_obj = {
                'route_id': route_id,
                'agency_id': route.get('agency_id'),
                'route_short_name': route.get('route_short_name'),
                'route_long_name': route.get('route_long_name'),
                'route_type': int(route.get('route_type', 2)),  # Default to rail (2)
                'route_color': route.get('route_color', ''),
                'route_text_color': route.get('route_text_color', ''),
                'train_id': f"{route.get('agency_id', '')}:{route.get('route_short_name', '')}",
                'headsign': route.get('route_long_name', ''),
                'trips': []  # Will be populated with trips data
            }
            
            routes.append(route_obj)
        
        # If we don't have route data, log an error
        if not routes:
            logging.error("No routes loaded from API, using fallback data")
            routes = generate_simulated_routes()
    
    except Exception as e:
        logging.error(f"Error loading route data: {e}")
        # Generate simulated routes as fallback
        routes = generate_simulated_routes()
    
    return routes

def connect_routes_with_trips(routes: List[Dict[str, Any]], trips: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Connect routes with their trips to get stop sequences.
    
    Args:
        routes (List[Dict[str, Any]]): List of route data
        trips (Dict[str, Dict[str, Any]]): Dictionary of trip data
        
    Returns:
        List[Dict[str, Any]]: Updated list of route data with trip information
    """
    for route in routes:
        route_id = route['route_id']
        route_trips = []
        
        # Find all trips for this route
        for trip_id, trip_data in trips.items():
            if trip_data['route_id'] == route_id:
                # If the trip has stops, add it to route's trips
                if trip_data['stops']:
                    route_trips.append({
                        'trip_id': trip_id,
                        'headsign': trip_data['trip_headsign'],
                        'stops': trip_data['stops']
                    })
        
        # Sort trips by the number of stops (more stops first)
        route_trips.sort(key=lambda x: len(x['stops']), reverse=True)
        
        # Add trips to route
        route['trips'] = route_trips
        
        # Extract station sequence from the first trip (most complete one)
        if route_trips:
            route['stations'] = [stop['stop_id'] for stop in route_trips[0]['stops']]
        else:
            route['stations'] = []
    
    # Filter out routes without any stops/stations
    routes = [route for route in routes if route['stations']]
    
    return routes

def get_simulated_route_stations(route_id: str) -> List[str]:
    """
    Get a list of stations for a route (simulated for demo).
    In a real implementation, this would query the trips and stop_times tables.
    
    Args:
        route_id (str): The route ID
        
    Returns:
        List[str]: List of station IDs
    """
    # Major Belgian stations to use for simulation
    major_stations = [
        "8811007",  # Gent-Sint-Pieters
        "8821006",  # Brussel-Zuid
        "8831005",  # Leuven
        "8831310",  # Antwerpen-Centraal
        "8841004",  # Oostende
        "8841608",  # Brugge
        "8844628",  # Kortrijk
        "8863008",  # Hasselt
        "8865003",  # Genk
        "8866001",  # Luik-Guillemins
        "8872009",  # Charleroi-Zuid
        "8883006",  # Namen
        "8884335",  # Doornik
        "8891405",  # Mechelen
        "8891660",  # Blankenberge
        "8891702",  # Gent-Dampoort
        "8892007",  # Denderleeuw
        "8893401",  # Aalst
        "8895505",  # Dendermonde
        "8896008",  # Poperinge
        "8896735",  # Ieper
    ]
    
    # Use hash of route_id to create a deterministic but seemingly random selection
    import hashlib
    seed = int(hashlib.md5(route_id.encode()).hexdigest(), 16) % 10000
    np.random.seed(seed)
    
    # Select origin and destination
    origin_idx = np.random.randint(0, len(major_stations))
    origin = major_stations[origin_idx]
    
    # Make sure destination is different from origin
    dest_idx = (origin_idx + 1 + np.random.randint(0, len(major_stations) - 1)) % len(major_stations)
    destination = major_stations[dest_idx]
    
    # Determine route direction
    if origin_idx < dest_idx:
        direction = 1
        stations_pool = major_stations[origin_idx+1:dest_idx]
    else:
        direction = -1
        stations_pool = major_stations[dest_idx+1:origin_idx]
    
    # Select intermediate stations
    num_intermediate = min(np.random.randint(1, 5), len(stations_pool))
    if direction == -1:
        stations_pool = stations_pool[::-1]
    
    if len(stations_pool) > 0 and num_intermediate > 0:
        intermediates = list(np.random.choice(
            stations_pool, 
            size=min(num_intermediate, len(stations_pool)), 
            replace=False
        ))
    else:
        intermediates = []
    
    # Construct full route
    if direction == 1:
        route_stations = [origin] + intermediates + [destination]
    else:
        route_stations = [destination] + intermediates + [origin]
    
    return route_stations

def generate_simulated_routes(num_routes=30) -> List[Dict[str, Any]]:
    """
    Generate simulated routes for testing.
    
    Args:
        num_routes (int): Number of routes to generate
        
    Returns:
        List[Dict[str, Any]]: List of route data
    """
    routes = []
    
    for i in range(num_routes):
        route_id = f"R{10000 + i}"
        agency_id = "NMBS"
        route_short_name = f"{100 + i}"
        
        # Select a random route type (mostly trains)
        route_types = [0, 1, 2, 3]  # 0=tram, 1=subway, 2=rail, 3=bus
        route_type_weights = [0.05, 0.05, 0.85, 0.05]  # 85% trains
        route_type = np.random.choice(route_types, p=route_type_weights)
        
        # Generate headsign based on origin and destination
        stations = get_simulated_route_stations(route_id)
        if len(stations) >= 2:
            origin_id = stations[0]
            dest_id = stations[-1]
            headsign = f"{origin_id} - {dest_id}"
        else:
            headsign = f"Route {route_short_name}"
        
        # Create route object
        route = {
            'route_id': route_id,
            'agency_id': agency_id,
            'route_short_name': route_short_name,
            'route_long_name': headsign,
            'route_type': route_type,
            'route_color': '',
            'route_text_color': '',
            'train_id': f"{agency_id}:{route_short_name}",
            'headsign': headsign,
            'stations': stations
        }
        
        routes.append(route)
    
    return routes

def get_route_color(index: int, total: int, route_type: int = 2) -> str:
    """
    Get a color for a route based on its index and type.
    
    Args:
        index (int): Index of the route
        total (int): Total number of routes
        route_type (int): Type of the route (0=tram, 1=subway, 2=rail, 3=bus)
        
    Returns:
        str: Hex color code
    """
    # Base color by route type
    base_colors = {
        0: '#FF9800',  # Tram: Orange
        1: '#673AB7',  # Subway: Purple
        2: '#2196F3',  # Rail: Blue
        3: '#4CAF50',  # Bus: Green
        4: '#F44336',  # Ferry: Red
        5: '#795548',  # Cable car: Brown
        6: '#607D8B',  # Gondola: Blue-grey
        7: '#9E9E9E',  # Funicular: Grey
    }
    
    # Get base color or default to blue
    base = base_colors.get(route_type, '#2196F3')
    
    # Convert hex to RGB
    r = int(base[1:3], 16) / 255
    g = int(base[3:5], 16) / 255
    b = int(base[5:7], 16) / 255
    
    # Convert RGB to HSV
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    # Vary the hue based on the index, but keep it close to the base color
    if total > 1:
        h_variation = 0.2  # 20% variation in hue
        h = (h + h_variation * (index / (total - 1) - 0.5)) % 1.0
    
    # Convert back to RGB
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    
    # Convert RGB to hex
    color = '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
    return color

def get_realtime_train_data() -> Dict[str, Dict[str, Any]]:
    """
    Get realtime train data from the API.
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of train data with train_id as key
    """
    realtime_trains = {}
    
    try:
        # Get realtime data
        realtime_data = get_realtime_data()
        
        # Check if API returned expected structure
        if not realtime_data or not isinstance(realtime_data, dict):
            logging.warning("Realtime API returned unexpected data format")
            return realtime_trains
            
        # Process entities if they exist
        entities = realtime_data.get('entity', [])
        
        # If no entities, try simulating realtime data (for testing)
        if not entities:
            logging.warning("No realtime entities found in API response, simulating 10 trains")
            return simulate_realtime_trains(10)
            
        # Process entities
        for entity in entities:
            # Extract train ID
            train_id = entity.get('id', '')
            if not train_id:
                continue
                
            # Get vehicle position if available
            vehicle = entity.get('vehicle', {})
            position = vehicle.get('position', {})
            
            lat = position.get('latitude')
            lon = position.get('longitude')
            
            # Skip entities without position
            if not lat or not lon:
                continue
                
            # Get current status
            current_status = vehicle.get('current_status', 0)
            status_map = {
                0: 'Incoming at stop',
                1: 'Stopped at stop',
                2: 'In transit to next stop'
            }
            status_text = status_map.get(current_status, 'Unknown')
            
            # Get delay in minutes
            delay_seconds = vehicle.get('delay', 0)
            delay_minutes = max(0, int(delay_seconds / 60))
            
            # Get trip details
            trip = vehicle.get('trip', {})
            trip_id = trip.get('trip_id', '')
            route_id = trip.get('route_id', '')
            
            # Store train data
            realtime_trains[train_id] = {
                'position': (lat, lon),
                'status': status_text,
                'delay': delay_minutes,
                'trip_id': trip_id,
                'route_id': route_id,
                'timestamp': datetime.datetime.now().isoformat()
            }
    
    except Exception as e:
        logging.error(f"Error getting realtime train data: {e}")
    
    return realtime_trains

def simulate_realtime_trains(num_trains=10) -> Dict[str, Dict[str, Any]]:
    """
    Simulate realtime train data for testing when API doesn't return data.
    
    Args:
        num_trains (int): Number of trains to simulate
        
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of simulated train data
    """
    import random
    
    # Belgium geographical boundaries (approx)
    min_lat, max_lat = 49.5, 51.5
    min_lon, max_lon = 2.5, 6.5
    
    simulated_trains = {}
    
    # Generate random train IDs and positions
    for i in range(num_trains):
        train_id = f"NMBS:{random.randint(100, 999)}"
        
        # Random position in Belgium
        lat = min_lat + random.random() * (max_lat - min_lat)
        lon = min_lon + random.random() * (max_lon - min_lon)
        
        # Random status and delay
        status_options = ['Incoming at stop', 'Stopped at stop', 'In transit to next stop']
        status = random.choice(status_options)
        delay = random.randint(0, 20)  # 0-20 minutes delay
        
        # Random route and trip IDs
        route_id = f"R{10000 + random.randint(1, 100)}"
        trip_id = f"T{20000 + random.randint(1, 100)}"
        
        # Store simulated train
        simulated_trains[train_id] = {
            'position': (lat, lon),
            'status': status,
            'delay': delay,
            'trip_id': trip_id,
            'route_id': route_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'simulated': True
        }
    
    logging.info(f"Generated {num_trains} simulated trains for testing")
    return simulated_trains

def create_realtime_train_routes_map(max_routes=20, save_path=None):
    """
    Create an interactive map showing realtime train routes.
    
    Args:
        max_routes (int): Maximum number of routes to display
        save_path (str): Path to save the map HTML file, or None to use default
        
    Returns:
        str: Path to the saved HTML map file
    """
    import colorsys
    import folium
    from folium.plugins import MarkerCluster, FeatureGroupSubGroup
    import datetime
    
    # Load station data
    stations = load_station_data()
    print(f"✓ Loaded {len(stations)} stations")
    
    # Load trips and stop_times data
    trips = load_trips_data()
    trips = load_stop_times_data(trips)
    
    # Load route data
    routes = load_route_data()
    print(f"✓ Loaded {len(routes)} routes")
    
    # Connect routes with trips to get stop sequences
    routes = connect_routes_with_trips(routes, trips)
    
    # Load realtime data
    realtime_data = get_realtime_train_data()
    print(f"✓ Loaded {len(realtime_data)} realtime trains")
    
    # Center the map on Belgium
    map_center = [50.85, 4.35]  # Brussels coordinates
    
    # Create a map
    train_map = folium.Map(
        location=map_center,
        zoom_start=8,
        tiles='CartoDB positron'
    )
    
    # Add title and timestamp
    title_html = f'''
        <h3 align="center" style="font-size:16px">
            <b>Belgian Railways (NMBS/SNCB) - Real-time Train Routes</b>
        </h3>
        <h4 align="center" style="font-size:14px">
            Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            <br><span style="font-size:12px">(API updates every 30 seconds)</span>
        </h4>
    '''
    train_map.get_root().html.add_child(folium.Element(title_html))
    
    # Create a marker cluster for stations
    station_cluster = MarkerCluster(name="All Stations")
    train_map.add_child(station_cluster)
    
    # Create a feature group for routes
    route_group = folium.FeatureGroup(name="All Routes")
    train_map.add_child(route_group)
    
    # Add stations to the map
    for station_id, station_info in stations.items():
        # Skip stations without valid coordinates
        if 'coords' not in station_info:
            continue
            
        lat, lon = station_info['coords']
        
        # Create popup content with station info
        popup_content = f"""
        <div style="min-width: 180px; max-width: 250px">
            <h4>{station_info['name']}</h4>
            <b>Station ID:</b> {station_id}<br>
            <b>Platforms:</b> {station_info.get('num_platforms', 'Unknown')}<br>
            <b>Coordinates:</b> {lat:.4f}, {lon:.4f}
        </div>
        """
        
        # Add marker with popup
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=station_info['name'],
            icon=folium.Icon(icon='train', prefix='fa', color='blue')
        ).add_to(station_cluster)
    
    # Filter and limit the number of routes to display
    active_routes = []
    
    # First, add routes with realtime data
    for train_id, train_info in realtime_data.items():
        route_id = train_info.get('route_id')
        for route in routes:
            if route['route_id'] == route_id:
                route['realtime'] = train_info
                active_routes.append(route)
                break
                
        # If no route found by route_id, try matching by train_id
        if not any(r.get('realtime') == train_info for r in active_routes):
            for route in routes:
                if route['train_id'] == train_id:
                    route['realtime'] = train_info
                    active_routes.append(route)
                    break
        
        # If we've reached the maximum, stop
        if len(active_routes) >= max_routes:
            break
    
    # If we still have space, add routes with most stops
    if len(active_routes) < max_routes:
        remaining_slots = max_routes - len(active_routes)
        existing_route_ids = {r['route_id'] for r in active_routes}
        
        # Sort the remaining routes by number of stations (most first)
        regular_routes = sorted(
            [r for r in routes if r['route_id'] not in existing_route_ids],
            key=lambda r: len(r.get('stations', [])),
            reverse=True
        )
        
        active_routes.extend(regular_routes[:remaining_slots])
    
    # Create a route-specific layer for each route
    for idx, route in enumerate(active_routes):
        # Get route details
        route_id = route['route_id']
        train_id = route['train_id']
        headsign = route.get('headsign', '')
        route_type = route.get('route_type', 2)  # Default to rail
        
        # Set route color
        route_color = get_route_color(idx, len(active_routes), route_type)
        
        # Create a route group for this specific route
        route_name = f"Route {route_id} - {headsign}" if headsign else f"Route {route_id}"
        route_specific_group = FeatureGroupSubGroup(
            route_group, 
            name=route_name
        )
        train_map.add_child(route_specific_group)
        
        # Get the station IDs for this route
        station_ids = route.get('stations', [])
        
        # Skip routes without enough stations
        if len(station_ids) < 2:
            continue
        
        # Create lists to store coordinates and station details
        route_coords = []
        valid_station_count = 0
        
        # Realtime info if available
        realtime_info = route.get('realtime', {})
        is_realtime = bool(realtime_info)
        current_position = realtime_info.get('position')
        current_status = realtime_info.get('status', 'No real-time data')
        current_delay = realtime_info.get('delay', 0)
        
        # Add each station to the route
        for i, station_id in enumerate(station_ids):
            if station_id in stations and 'coords' in stations[station_id]:
                valid_station_count += 1
                station_info = stations[station_id]
                lat, lon = station_info['coords']
                route_coords.append([lat, lon])
                
                # Station status
                is_first = i == 0
                is_last = i == len(station_ids) - 1
                
                # Determine station type
                if is_first:
                    station_type = "Origin"
                    icon_color = "green"
                elif is_last:
                    station_type = "Destination" 
                    icon_color = "red"
                else:
                    station_type = "Stop"
                    icon_color = "orange"
                
                # Create popup with detailed route information
                popup_content = f"""
                <div style="min-width: 200px; max-width: 300px">
                    <h4>{station_info['name']} ({station_type})</h4>
                    <b>Route:</b> {route_id}<br>
                    <b>Train ID:</b> {train_id}<br>
                    <b>Direction:</b> {headsign}<br>
                    <hr>
                    <b>Stop sequence:</b> {i+1} of {len(station_ids)}<br>
                """
                
                # Add realtime information if available
                if is_realtime:
                    popup_content += f"""
                    <hr>
                    <b>Real-time Status:</b> {current_status}<br>
                    <b>Current Delay:</b> {current_delay} minutes<br>
                    """
                
                popup_content += "</div>"
                
                # Add marker for station
                station_marker = folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"{station_info['name']} ({station_type})",
                    icon=folium.Icon(icon='circle', prefix='fa', color=icon_color)
                )
                station_marker.add_to(route_specific_group)
        
        # Skip routes without enough valid stations
        if valid_station_count < 2:
            continue
            
        # Create route line
        route_line = folium.PolyLine(
            route_coords,
            color=route_color,
            weight=3,
            opacity=0.8,
            tooltip=f"Route {route_id} - {headsign}"
        )
        route_line.add_to(route_specific_group)
        
        # Add train icon for current position if realtime data available
        if is_realtime and current_position:
            pos_lat, pos_lon = current_position
            
            # Create detailed popup for the train
            train_popup = f"""
            <div style="min-width: 250px; max-width: 350px">
                <h4>Train {train_id}</h4>
                <b>Route:</b> {route_id}<br>
                <b>Direction:</b> {headsign}<br>
                <hr>
                <b>Current Status:</b> {current_status}<br>
                <b>Current Delay:</b> {current_delay} minutes<br>
                <b>Position:</b> {pos_lat:.4f}, {pos_lon:.4f}<br>
                <hr>
                <b>Origin:</b> {stations[station_ids[0]]['name'] if station_ids[0] in stations else "Unknown"}<br>
                <b>Destination:</b> {stations[station_ids[-1]]['name'] if station_ids[-1] in stations else "Unknown"}<br>
                <hr>
                <button onclick="window.open('https://www.belgiantrain.be/en/travel-info/search-a-train?trainNumber={train_id.split(':')[-1] if ':' in train_id else train_id}', '_blank')">
                    View on NMBS/SNCB Website
                </button>
            </div>
            """
            
            # Add train marker with custom icon
            train_icon = folium.Icon(
                icon='subway',
                prefix='fa',
                color='darkred',
                icon_color='white'
            )
            
            train_marker = folium.Marker(
                [pos_lat, pos_lon],
                popup=folium.Popup(train_popup, max_width=350),
                tooltip=f"Train {train_id} ({current_status})",
                icon=train_icon
            )
            train_marker.add_to(route_specific_group)
    
    # Add layer control
    folium.LayerControl().add_to(train_map)

    # Determine save path
    if not save_path:
        timestamp = int(time.time())
        maps_dir = os.path.join('reports', 'maps')
        os.makedirs(maps_dir, exist_ok=True)
        save_path = os.path.join(maps_dir, f'train_routes_{timestamp}.html')

    # Save the map
    train_map.save(save_path)
    print(f"Map saved to: {save_path}")
    
    return save_path

def create_trajectories_map(max_trajectories=30, save_path=None, light_mode=False, pages_to_fetch=-1):
    """
    Create an interactive map showing train trajectories from the new API endpoint.
    
    Args:
        max_trajectories (int): Maximum number of trajectories to display on the map
                               (set to float('inf') for no limit)
        save_path (str): Path to save the map HTML file, or None to use default
        light_mode (bool): Whether to use light mode for the map
        pages_to_fetch (int): Number of pages to fetch from the API, -1 for all pages
        
    Returns:
        str: Path to the saved HTML map file
    """
    import folium
    from folium.plugins import MarkerCluster, FeatureGroupSubGroup, TimestampedGeoJson
    import datetime
    import time
    import random
    import colorsys
    from nmbs_data.data.api_client import get_trajectories_data
    
    # Load trajectories data from the API
    trajectories_response = get_trajectories_data(max_pages=pages_to_fetch)
    trajectories = trajectories_response.get('data', [])
    
    if not trajectories:
        print("⚠️ No trajectories data found from API.")
        return None
    
    # Get metadata
    metadata = trajectories_response.get('metadata', {})
    generated_at = metadata.get('generated_at', datetime.datetime.now().isoformat())
    total_records = metadata.get('total_records', len(trajectories))
    
    print(f"✓ Loaded {len(trajectories)} trajectories from API (out of {total_records} total records)")
    
    # Select a subset of trajectories if needed (unless max_trajectories is infinite)
    if len(trajectories) > max_trajectories and max_trajectories != float('inf'):
        print(f"⚠️ Limiting display to {max_trajectories} trajectories for performance (out of {len(trajectories)} loaded)")
        # Prioritize trajectories with more stops for better visualization
        trajectories.sort(key=lambda t: len(t.get('stops', [])), reverse=True)
        trajectories = trajectories[:max_trajectories]
    elif max_trajectories == float('inf'):
        print(f"ℹ️ Displaying all {len(trajectories)} trajectories (no limit applied)")
    
    # Center the map on Belgium
    map_center = [50.85, 4.35]  # Brussels coordinates
    
    # Create map with appropriate style
    if light_mode:
        map_tiles = 'CartoDB positron'
        map_bg = 'light'
    else:
        map_tiles = 'CartoDB dark_matter'
        map_bg = 'dark'
    
    train_map = folium.Map(
        location=map_center,
        zoom_start=8,
        tiles=map_tiles
    )
    
    # Add title and timestamp
    title_html = f'''
        <h3 align="center" style="font-size:16px; {'color:#fff' if map_bg == 'dark' else ''}">
            <b>Belgian Railways (NMBS/SNCB) - Train Trajectories</b>
        </h3>
        <h4 align="center" style="font-size:14px; {'color:#ddd' if map_bg == 'dark' else ''}">
            Data from: {generated_at}
            <br><span style="font-size:12px">Showing {len(trajectories)} of {total_records} trajectories | (API updates every 30 seconds)</span>
        </h4>
    '''
    train_map.get_root().html.add_child(folium.Element(title_html))
    
    # Create feature groups for organization
    stations_group = folium.FeatureGroup(name="All Stations")
    train_map.add_child(stations_group)
    
    all_routes_group = folium.FeatureGroup(name="All Routes", show=False)
    train_map.add_child(all_routes_group)
    
    active_trains_group = folium.FeatureGroup(name="Active Trains")
    train_map.add_child(active_trains_group)
    
    # Dictionary to store unique stations to avoid duplicates
    unique_stations = {}
    
    # Process each trajectory
    for idx, trajectory in enumerate(trajectories):
        # Extract basic information
        entity_id = trajectory.get('entity_id', 'unknown')
        trip_id = trajectory.get('trip_id', 'unknown')
        
        # Get route information
        route = trajectory.get('route', {})
        route_id = route.get('route_id', 'unknown')
        route_type = route.get('route_type', 'IC')
        route_name = route.get('route_name', f'Route {route_id}')
        agency_id = route.get('agency_id', 'NMBS/SNCB')
        
        # Get trip details
        trip = trajectory.get('trip', {})
        trip_number = trip.get('trip_number', 'unknown')
        trip_headsign = trip.get('trip_headsign', 'unknown')
        service_id = trip.get('service_id', 'unknown')
        
        # Get stops
        stops = trajectory.get('stops', [])
        if not stops or len(stops) < 2:
            continue
        
        # Generate a color for this trajectory
        hue = (idx * 0.618033988749895) % 1.0  # Golden ratio distribution
        if map_bg == 'dark':
            r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 1.0)
        else:
            r, g, b = colorsys.hsv_to_rgb(hue, 0.7, 0.8)
        color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
        
        # Create a subgroup for this trajectory
        route_display_name = f"{route_type} {trip_number}: {route_name}"
        route_group = FeatureGroupSubGroup(all_routes_group, name=route_display_name)
        train_map.add_child(route_group)
        
        # Prepare coordinates for polyline
        route_coords = []
        stop_features = []
        
        # Current time for comparison
        current_time = int(time.time())
        
        # Find the most recent stop with departure/arrival time in the past
        current_stop_index = -1
        for i, stop in enumerate(stops):
            # Check departure time if available
            departure = stop.get('departure')
            if departure:
                timestamp = int(departure.get('timestamp', 0))
                if timestamp <= current_time:
                    current_stop_index = i
            
            # If no departure or it's in the future, check arrival
            if current_stop_index != i:
                arrival = stop.get('arrival')
                if arrival:
                    timestamp = int(arrival.get('timestamp', 0))
                    if timestamp <= current_time:
                        current_stop_index = i
        
        # Process each stop
        for i, stop in enumerate(stops):
            # Extract station information
            station = stop.get('station', {})
            station_name = station.get('name', f'Station {i}')
            
            # Get translations if available
            translations = station.get('translations', {})
            dutch_name = translations.get('nl', station_name)
            english_name = translations.get('en', station_name)
            
            # Get location
            location = station.get('location', {})
            lat = float(location.get('latitude', 0))
            lon = float(location.get('longitude', 0))
            
            # Skip stops without valid coordinates
            if lat == 0 and lon == 0:
                continue
                
            # Add to coordinates list for route line
            route_coords.append([lat, lon])
            
            # Determine if this is the current stop
            is_current = (i == current_stop_index)
            
            # Add station to unique stations dictionary if not already present
            station_id = stop.get('stop_id', f'stop_{i}')
            if station_id not in unique_stations:
                station_icon = folium.Icon(
                    icon='train-station', 
                    prefix='fa', 
                    color='blue'
                )
                
                popup_html = f"""
                <div style="min-width: 180px; max-width: 250px">
                    <h4>{station_name}</h4>
                    <b>ID:</b> {station_id}<br>
                    {f"<b>Dutch:</b> {dutch_name}<br>" if dutch_name != station_name else ""}
                    {f"<b>English:</b> {english_name}<br>" if english_name != station_name else ""}
                    <b>Coordinates:</b> {lat:.4f}, {lon:.4f}
                </div>
                """
                
                # Create station marker
                station_marker = folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=station_name,
                    icon=station_icon
                )
                unique_stations[station_id] = {
                    'marker': station_marker,
                    'name': station_name,
                    'coords': (lat, lon)
                }
                station_marker.add_to(stations_group)
            
            # Determine status icon and color based on position in sequence
            if i == 0:
                stop_type = "Origin"
                icon_color = "green"
            elif i == len(stops) - 1:
                stop_type = "Destination"
                icon_color = "red"
            else:
                stop_type = "Stop"
                icon_color = "orange" if is_current else "blue"
            
            # Extract timing information
            arrival = stop.get('arrival', {})
            departure = stop.get('departure', {})
            
            # Format arrival info
            arrival_time = "N/A"
            arrival_delay = "N/A"
            if arrival:
                arrival_time = arrival.get('datetime', 'N/A')
                arrival_delay = arrival.get('status', 'on time')
            
            # Format departure info
            departure_time = "N/A"
            departure_delay = "N/A"
            if departure:
                departure_time = departure.get('datetime', 'N/A')
                departure_delay = departure.get('status', 'on time')
            
            # Create detailed popup for this stop
            popup_content = f"""
            <div style="min-width: 220px; max-width: 300px">
                <h4>{station_name} ({stop_type})</h4>
                <b>Train:</b> {route_type} {trip_number}<br>
                <b>Route:</b> {route_name}<br>
                <b>Direction:</b> {trip_headsign}<br>
                <hr>
                <b>Stop sequence:</b> {i+1} of {len(stops)}<br>
                <hr>
                <b>Arrival:</b> {arrival_time}<br>
                <b>Arrival status:</b> {arrival_delay}<br>
                <b>Departure:</b> {departure_time}<br>
                <b>Departure status:</b> {departure_delay}<br>
            </div>
            """
            
            # Create a stop marker for this specific route
            stop_icon = folium.Icon(
                icon='circle', 
                prefix='fa', 
                color=icon_color
            )
            
            # Add a marker for this stop
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"{station_name} ({stop_type})",
                icon=stop_icon
            ).add_to(route_group)
        
        # Skip routes without enough valid stops
        if len(route_coords) < 2:
            continue
            
        # Create route line
        route_line = folium.PolyLine(
            route_coords,
            color=color,
            weight=4,
            opacity=0.8,
            tooltip=f"{route_type} {trip_number}: {route_name}"
        )
        route_line.add_to(route_group)
        
        # Add a train icon at the current position if we know it
        if current_stop_index >= 0 and current_stop_index < len(route_coords):
            current_pos = route_coords[current_stop_index]
            
            # If we're between stops, interpolate position
            if current_stop_index < len(route_coords) - 1:
                next_pos = route_coords[current_stop_index + 1]
                
                # Get departure time from current stop
                current_stop = stops[current_stop_index]
                next_stop = stops[current_stop_index + 1]
                
                departure_time = None
                if current_stop.get('departure'):
                    departure_time = int(current_stop['departure'].get('timestamp', 0))
                
                arrival_time = None
                if next_stop.get('arrival'):
                    arrival_time = int(next_stop['arrival'].get('timestamp', 0))
                
                # Only interpolate if we have valid times
                if departure_time and arrival_time and departure_time < current_time < arrival_time:
                    # Calculate progress between stops (0.0 to 1.0)
                    progress = (current_time - departure_time) / (arrival_time - departure_time)
                    
                    # Interpolate position
                    lat = current_pos[0] + progress * (next_pos[0] - current_pos[0])
                    lon = current_pos[1] + progress * (next_pos[1] - current_pos[1])
                    
                    current_pos = [lat, lon]
            
            # Get current and next stop info for popup
            current_stop = stops[current_stop_index]
            current_station = current_stop.get('station', {}).get('name', 'Unknown')
            
            next_station = "Terminus"
            if current_stop_index < len(stops) - 1:
                next_station = stops[current_stop_index + 1].get('station', {}).get('name', 'Unknown')
            
            # Get delay info for current stop
            delay_minutes = 0
            status = "On time"
            
            # Check departure delay if available
            if current_stop.get('departure'):
                delay_minutes = current_stop['departure'].get('delay_minutes', 0)
                status = current_stop['departure'].get('status', 'On time')
            # Otherwise check arrival delay
            elif current_stop.get('arrival'):
                delay_minutes = current_stop['arrival'].get('delay_minutes', 0)
                status = current_stop['arrival'].get('status', 'On time')
            
            # Create detailed popup for the train
            train_popup = f"""
            <div style="min-width: 250px; max-width: 350px">
                <h4>{route_type} {trip_number}</h4>
                <b>Route:</b> {route_name}<br>
                <b>Direction:</b> {trip_headsign}<br>
                <hr>
                <b>Current status:</b> {status}<br>
                <b>Delay:</b> {delay_minutes} minutes<br>
                <hr>
                <b>Current/Last station:</b> {current_station}<br>
                <b>Next station:</b> {next_station}<br>
                <hr>
                <b>Total stops:</b> {len(stops)}<br>
                <button onclick="window.open('https://www.belgiantrain.be/en/travel-info/search-a-train?trainNumber={trip_number}', '_blank')">
                    View on NMBS/SNCB Website
                </button>
            </div>
            """
            
            # Choose icon color based on delay
            icon_color = 'green'
            if delay_minutes > 0:
                icon_color = 'orange'
            if delay_minutes >= 5:
                icon_color = 'red'
            
            # Add train marker with custom icon
            train_icon = folium.Icon(
                icon='train',
                prefix='fa',
                color=icon_color,
                icon_color='white'
            )
            
            train_marker = folium.Marker(
                current_pos,
                popup=folium.Popup(train_popup, max_width=350),
                tooltip=f"{route_type} {trip_number} to {trip_headsign}",
                icon=train_icon
            )
            train_marker.add_to(active_trains_group)
    
    # Add layer control
    folium.LayerControl(collapsed=False).add_to(train_map)
    
    # Add fullscreen button
    folium.plugins.Fullscreen().add_to(train_map)
    
    # Add a legend
    legend_html = f'''
    <div style="position: fixed; 
        bottom: 50px; left: 50px; width: 180px; height: 125px; 
        border:2px solid {'white' if map_bg == 'dark' else 'black'}; 
        z-index:9999; 
        background-color: {'rgba(32, 32, 32, 0.8)' if map_bg == 'dark' else 'rgba(255, 255, 255, 0.8)'}; 
        {'color: white;' if map_bg == 'dark' else ''}">
        <div style="font-size: 14px; padding: 8px;">
        <b>Legend</b><br>
        <i class="fa fa-train" style="color:green;"></i> On time train<br>
        <i class="fa fa-train" style="color:orange;"></i> Delayed train (< 5 min)<br>
        <i class="fa fa-train" style="color:red;"></i> Delayed train (≥ 5 min)<br>
        <i class="fa fa-circle" style="color:green;"></i> Origin station<br>
        <i class="fa fa-circle" style="color:red;"></i> Destination station<br>
        <i class="fa fa-circle" style="color:orange;"></i> Current stop<br>
        </div>
    </div>
    '''
    train_map.get_root().html.add_child(folium.Element(legend_html))
    
    # Add auto-refresh capability for real-time updates
    refresh_html = '''
    <script>
        // Auto-refresh the map every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
    '''
    train_map.get_root().html.add_child(folium.Element(refresh_html))

    # Determine save path
    if not save_path:
        timestamp = int(time.time())
        maps_dir = os.path.join('reports', 'maps')
        os.makedirs(maps_dir, exist_ok=True)
        save_path = os.path.join(maps_dir, f'train_trajectories_{timestamp}.html')

    # Save the map
    train_map.save(save_path)
    print(f"Trajectory map saved to: {save_path}")
    
    return save_path

if __name__ == "__main__":
    # When run directly, generate a map using default settings
    map_path = create_realtime_train_routes_map()
    print(f"To view the map, open: {map_path}")

