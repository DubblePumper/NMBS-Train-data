"""
Module for reading GTFS real-time data from Protocol Buffer files.
"""

import os
import json
import datetime
from pathlib import Path
import random
import struct
from google.transit import gtfs_realtime_pb2
import requests  # Import the GTFS-realtime protocol buffer

from .data_paths import get_realtime_dirs

def read_specific_realtime_files(file_paths=None):
    """
    Read specific GTFS real-time files using protocol buffer parsing.
    
    Args:
        file_paths: Optional list of file paths to read. If None, attempts to read 
                   from standard directories.
                    
    Returns:
        Dictionary containing parsed data organized by data source.
    """
    result = {
        'with_platform_changes': {},
        'without_platform_changes': {}
    }
    
    try:
        # If no specific file paths are provided, use the existing bin files
        if file_paths is None:
            realtime_dirs = get_realtime_dirs()
            
            # Use the existing bin files instead of looking for any .pb or .bin files
            existing_files = [
                os.path.join(os.path.dirname(realtime_dirs[0]), "real-time_gegevens_met_info_over_spoorveranderingen.bin"),
                os.path.join(os.path.dirname(realtime_dirs[1]), "real-time_gegevens_zonder_info_over_spoorveranderingen.bin")
            ]
            
            file_paths = [f for f in existing_files if os.path.exists(f)]
        
        if not file_paths:
            print("No GTFS real-time files found.")
            return result
        
        # Process each file using the GTFS-realtime protocol buffer
        for file_path in file_paths:
            try:
                # Determine which category this file belongs to
                if "met_info_over_spoorveranderingen" in file_path:
                    category = 'with_platform_changes'
                else:
                    category = 'without_platform_changes'
                
                # Read and parse the protocol buffer file
                feed = gtfs_realtime_pb2.FeedMessage()
                with open(file_path, 'rb') as f:
                    feed.ParseFromString(f.read())
                
                # Store the parsed data in the result dictionary
                filename = os.path.basename(file_path)
                result[category][filename] = {
                    'feed': feed,
                    'file_path': file_path,
                    'entity_count': len(feed.entity),
                    'header': {
                        'timestamp': feed.header.timestamp,
                        'version': feed.header.gtfs_realtime_version
                    },
                    'file_info': {
                        'size_bytes': os.path.getsize(file_path),
                        'last_modified': datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }
                }
                
                print(f"Successfully loaded GTFS real-time data from: {filename}")
                print(f"Found {len(feed.entity)} entities in the feed")
                
            except Exception as e:
                print(f"Error parsing GTFS-realtime file {file_path}: {e}")
        
        return result
    except Exception as e:
        print(f"Error reading GTFS real-time files: {e}")
        return result

def extract_vehicle_positions(realtime_data):
    """
    Extract vehicle positions from GTFS real-time data.
    
    Args:
        realtime_data: Dictionary containing real-time data
        
    Returns:
        list: List of vehicle position dictionaries with lat/lon coordinates
    """
    positions = []
    
    try:
        for data_source, rt_data in realtime_data.items():
            # Process each file in the data source category
            for filename, file_data in rt_data.items():
                # Check if this is properly parsed GTFS-realtime data
                if 'feed' in file_data:
                    feed = file_data['feed']
                    
                    for entity in feed.entity:
                        # Check if this entity has vehicle position information
                        if entity.HasField('vehicle'):
                            vehicle = entity.vehicle
                            
                            # Extract basic position data
                            position_data = {
                                "trip_id": vehicle.trip.trip_id if vehicle.HasField('trip') else "Unknown",
                                "route_id": vehicle.trip.route_id if vehicle.HasField('trip') else "Unknown",
                                "vehicle_id": vehicle.vehicle.id if vehicle.HasField('vehicle') else "Unknown",
                                "latitude": vehicle.position.latitude if vehicle.HasField('position') else 0,
                                "longitude": vehicle.position.longitude if vehicle.HasField('position') else 0,
                                "bearing": vehicle.position.bearing if (vehicle.HasField('position') and vehicle.position.HasField('bearing')) else None,
                                "speed": vehicle.position.speed if (vehicle.HasField('position') and vehicle.position.HasField('speed')) else 0,
                                "timestamp": datetime.datetime.fromtimestamp(vehicle.timestamp).isoformat() if vehicle.HasField('timestamp') else datetime.datetime.now().isoformat(),
                                "has_platform_change": "met_info_over_spoorveranderingen" in filename,
                                "status": str(vehicle.current_status) if vehicle.HasField('current_status') else "UNKNOWN"
                            }
                            
                            positions.append(position_data)
        
        # If no positions were found in the actual data, provide a fallback with at least one position
        if not positions:
            print("Warning: No vehicle positions found in GTFS-realtime data. Using fallback position.")
            # Generate a fallback position in Brussels
            positions.append({
                "trip_id": "FALLBACK_TRIP",
                "route_id": "FALLBACK_ROUTE",
                "vehicle_id": "FALLBACK_VEHICLE",
                "latitude": 50.8503,  # Brussels
                "longitude": 4.3517,
                "bearing": 0,
                "speed": 0,
                "status": "UNKNOWN",
                "timestamp": datetime.datetime.now().isoformat(),
                "has_platform_change": False
            })
    except Exception as e:
        print(f"Error extracting vehicle positions: {e}")
        # Return a single fallback position so the visualization doesn't fail
        positions.append({
            "trip_id": "ERROR_FALLBACK",
            "route_id": "ERROR_ROUTE",
            "vehicle_id": "ERROR_VEHICLE",
            "latitude": 50.8503,  # Brussels
            "longitude": 4.3517,
            "bearing": 0,
            "speed": 0,
            "status": "ERROR",
            "timestamp": datetime.datetime.now().isoformat(),
            "has_platform_change": False
        })
    
    return positions

def create_sample_files():
    """
    This function is now deprecated since we're using existing bin files.
    Returns a message indicating this.
    """
    print("NOTE: Using existing real-time data files instead of creating new samples.")
    print("Using files:")
    print("- real-time_gegevens_met_info_over_spoorveranderingen.bin")
    print("- real-time_gegevens_zonder_info_over_spoorveranderingen.bin")
    return True