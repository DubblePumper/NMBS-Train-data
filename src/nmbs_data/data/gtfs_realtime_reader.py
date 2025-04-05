"""
Module for reading GTFS real-time data from the NMBS API.
This module only uses API calls, no local files are accessed.
"""

import logging
import requests
import json
import os
import datetime
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base API URL
BASE_URL = "https://nmbsapi.sanderzijntestjes.be/api/"

def get_realtime_data():
    """Get real-time data from the API.
    
    Returns:
        dict: Real-time data as a dictionary
    """
    try:
        url = urljoin(BASE_URL, "realtime/data")
        logger.info(f"Fetching real-time data from {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched real-time data with {len(data.get('entity', []))} entities")
        return data
    except Exception as e:
        logger.error(f"Error fetching real-time data: {str(e)}")
        return {"error": str(e)}

def extract_vehicle_positions(realtime_data):
    """Extract vehicle positions from real-time data.
    
    Args:
        realtime_data: Real-time data dictionary
        
    Returns:
        list: List of vehicle positions
    """
    positions = []
    
    # Handle the case where real-time data is a dictionary with keys like 'with_platform_changes'
    if isinstance(realtime_data, dict):
        # Check if this is direct API data
        if 'entity' in realtime_data:
            entities = realtime_data.get('entity', [])
            for entity in entities:
                if 'vehicle' in entity:
                    vehicle = entity['vehicle']
                    position = {
                        'trip_id': vehicle.get('trip', {}).get('trip_id', 'Unknown'),
                        'latitude': vehicle.get('position', {}).get('latitude', 0),
                        'longitude': vehicle.get('position', {}).get('longitude', 0),
                        'bearing': vehicle.get('position', {}).get('bearing', 0),
                        'speed': vehicle.get('position', {}).get('speed', 0),
                        'vehicle_id': vehicle.get('vehicle', {}).get('id', 'Unknown'),
                        'timestamp': vehicle.get('timestamp', 0)
                    }
                    positions.append(position)
        # Process nested structure
        else:
            for category, data in realtime_data.items():
                if isinstance(data, dict) and 'entity' in data:
                    # Extract from nested data
                    for entity in data.get('entity', []):
                        if 'vehicle' in entity:
                            vehicle = entity['vehicle']
                            position = {
                                'trip_id': vehicle.get('trip', {}).get('trip_id', 'Unknown'),
                                'latitude': vehicle.get('position', {}).get('latitude', 0),
                                'longitude': vehicle.get('position', {}).get('longitude', 0),
                                'bearing': vehicle.get('position', {}).get('bearing', 0),
                                'speed': vehicle.get('position', {}).get('speed', 0),
                                'vehicle_id': vehicle.get('vehicle', {}).get('id', 'Unknown'),
                                'timestamp': vehicle.get('timestamp', 0)
                            }
                            positions.append(position)
    
    logger.info(f"Extracted {len(positions)} vehicle positions from real-time data")
    return positions

def read_specific_realtime_files():
    """Get real-time data from the API with both platform changes and without platform changes.
    
    Returns:
        dict: Dictionary with two keys: 'with_platform_changes' and 'without_platform_changes',
              each containing the respective real-time data
    """
    # Get real-time data from the API
    try:
        realtime_data = get_realtime_data()
        
        if 'error' in realtime_data:
            return {
                'with_platform_changes': {'error': realtime_data['error']},
                'without_platform_changes': {'error': realtime_data['error']}
            }
        
        # Process the real-time data to separate entities with platform changes
        # This is just a placeholder logic - in real API, we might need different logic
        with_changes = {'entity': []}
        without_changes = {'entity': []}
        
        for entity in realtime_data.get('entity', []):
            has_platform_change = False
            
            # Check if this entity has platform changes
            if 'tripUpdate' in entity and 'stopTimeUpdate' in entity['tripUpdate']:
                for stop_update in entity['tripUpdate']['stopTimeUpdate']:
                    # In GTFS-RT, platform changes might be indicated in various ways
                    if 'platform_changed' in stop_update and stop_update['platform_changed']:
                        has_platform_change = True
                        break
                    
                    # Alternative check if scheduled platform != actual platform
                    if ('scheduled_platform' in stop_update and 'actual_platform' in stop_update and
                        stop_update['scheduled_platform'] != stop_update['actual_platform']):
                        has_platform_change = True
                        break
            
            # Sort the entity based on whether it has platform changes
            if has_platform_change:
                with_changes['entity'].append(entity)
            else:
                without_changes['entity'].append(entity)
        
        logger.info(f"Processed real-time data: {len(with_changes['entity'])} entities with platform changes, "
                    f"{len(without_changes['entity'])} entities without platform changes")
                
        return {
            'with_platform_changes': with_changes,
            'without_platform_changes': without_changes
        }
        
    except Exception as e:
        logger.error(f"Error processing real-time data: {str(e)}")
        return {
            'with_platform_changes': {'error': str(e)},
            'without_platform_changes': {'error': str(e)}
        }

def create_sample_files(realtime_dirs=None, num_samples=3, num_entities=5):
    """Create sample real-time data files for testing purposes.
    
    This function creates sample GTFS-RT data files that mimic the structure of real data
    but with simulated values. Useful for testing and demonstration when API access is limited.
    
    Args:
        realtime_dirs: Dictionary of real-time data directories (optional)
        num_samples: Number of sample files to create (default: 3)
        num_entities: Number of entities per sample file (default: 5)
        
    Returns:
        dict: Dictionary with paths to the created sample files
    """
    from nmbs_data.data.data_paths import get_realtime_dirs
    
    # Get real-time directories if not provided
    if realtime_dirs is None:
        realtime_dirs = get_realtime_dirs()
    
    # Ensure the directories exist
    created_files = {
        'with_platform_changes': [],
        'without_platform_changes': []
    }
    
    # Define major Belgian cities for sample data
    cities = [
        {"name": "Brussels", "lat": 50.8476, "lon": 4.3572},
        {"name": "Antwerp", "lat": 51.2213, "lon": 4.4051},
        {"name": "Ghent", "lat": 51.0543, "lon": 3.7174},
        {"name": "Liege", "lat": 50.6326, "lon": 5.5797},
        {"name": "Bruges", "lat": 51.2093, "lon": 3.2247},
        {"name": "Namur", "lat": 50.4673, "lon": 4.8719},
        {"name": "Leuven", "lat": 50.8798, "lon": 4.7005},
        {"name": "Mons", "lat": 50.4542, "lon": 3.9563},
        {"name": "Ostend", "lat": 51.2132, "lon": 2.9290},
        {"name": "Charleroi", "lat": 50.4108, "lon": 4.4444}
    ]
    
    # Train types
    train_types = ["IC", "IR", "S", "L", "P"]
    
    # Create sample files for both categories
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        for category in ['with_platform_changes', 'without_platform_changes']:
            # Get directory for this category
            category_dir = realtime_dirs.get(category.replace('_', ''))
            
            for i in range(num_samples):
                # Create a unique filename
                filename = f"sample_realtime_{timestamp}_{i+1}.json"
                file_path = os.path.join(category_dir, filename)
                
                # Generate sample data
                sample_data = {
                    "header": {
                        "gtfs_realtime_version": "2.0",
                        "incrementality": 0,
                        "timestamp": int(datetime.datetime.now().timestamp())
                    },
                    "entity": []
                }
                
                # Add sample entities
                for j in range(num_entities):
                    # Pick random cities for origin and destination
                    from_city = cities[j % len(cities)]
                    to_city = cities[(j + 3) % len(cities)]
                    
                    # Create entity ID
                    entity_id = f"sample-{i+1}-{j+1}"
                    
                    # Create train ID
                    train_type = train_types[j % len(train_types)]
                    train_number = 1000 + j
                    train_id = f"{train_type}{train_number}"
                    
                    # Create entity
                    entity = {
                        "id": entity_id,
                        "vehicle": {
                            "trip": {
                                "trip_id": train_id,
                                "route_id": f"route-{train_type}"
                            },
                            "position": {
                                "latitude": from_city["lat"] + (j * 0.01),
                                "longitude": from_city["lon"] + (j * 0.01),
                                "bearing": (j * 45) % 360
                            },
                            "vehicle": {
                                "id": f"vehicle-{train_id}"
                            },
                            "timestamp": int(datetime.datetime.now().timestamp()) - (j * 60)
                        }
                    }
                    
                    # For the 'with_platform_changes' category, add platform changes
                    if category == 'with_platform_changes':
                        entity["tripUpdate"] = {
                            "trip": {
                                "trip_id": train_id,
                                "route_id": f"route-{train_type}"
                            },
                            "stopTimeUpdate": [
                                {
                                    "stop_id": f"stop-{from_city['name'].lower()}",
                                    "departure_time": int(datetime.datetime.now().timestamp()) + 300,
                                    "scheduled_platform": str(j + 1),
                                    "actual_platform": str(j + 2),
                                    "platform_changed": True
                                },
                                {
                                    "stop_id": f"stop-{to_city['name'].lower()}",
                                    "arrival_time": int(datetime.datetime.now().timestamp()) + 1800,
                                    "scheduled_platform": str(j + 3),
                                    "actual_platform": str(j + 3),
                                    "platform_changed": False
                                }
                            ]
                        }
                    else:
                        # For 'without_platform_changes', platforms are the same
                        entity["tripUpdate"] = {
                            "trip": {
                                "trip_id": train_id,
                                "route_id": f"route-{train_type}"
                            },
                            "stopTimeUpdate": [
                                {
                                    "stop_id": f"stop-{from_city['name'].lower()}",
                                    "departure_time": int(datetime.datetime.now().timestamp()) + 300,
                                    "scheduled_platform": str(j + 1),
                                    "actual_platform": str(j + 1),
                                    "platform_changed": False
                                },
                                {
                                    "stop_id": f"stop-{to_city['name'].lower()}",
                                    "arrival_time": int(datetime.datetime.now().timestamp()) + 1800,
                                    "scheduled_platform": str(j + 3),
                                    "actual_platform": str(j + 3),
                                    "platform_changed": False
                                }
                            ]
                        }
                    
                    # Add the entity to the sample data
                    sample_data["entity"].append(entity)
                
                # Write sample data to file
                with open(file_path, 'w') as f:
                    json.dump(sample_data, f, indent=2)
                
                # Add file path to created files
                created_files[category].append(file_path)
                logger.info(f"Created sample file: {file_path}")
        
        logger.info(f"Created {num_samples} sample files for each category")
        return created_files
    
    except Exception as e:
        logger.error(f"Error creating sample files: {str(e)}")
        return {"error": str(e)}