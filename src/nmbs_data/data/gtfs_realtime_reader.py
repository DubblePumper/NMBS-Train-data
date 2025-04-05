"""
Module for reading GTFS real-time data from the NMBS API.
This module only uses API calls, no local files are accessed.
"""

import logging
import requests
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