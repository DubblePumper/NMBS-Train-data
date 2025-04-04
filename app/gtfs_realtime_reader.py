"""
Module for reading and processing GTFS real-time data.
GTFS (General Transit Feed Specification) real-time data is typically distributed as Protocol Buffer (.pb) files.
"""

import os
import glob
import pandas as pd
import datetime
from pathlib import Path
import json

try:
    from google.transit import gtfs_realtime_pb2
    GTFS_RT_AVAILABLE = True
except ImportError:
    print("Warning: gtfs-realtime-bindings not installed. GTFS real-time data processing will be limited.")
    print("Install with: pip install gtfs-realtime-bindings")
    GTFS_RT_AVAILABLE = False

# Fix import for data_paths
try:
    from app.data_paths import get_realtime_dirs
except ImportError:
    try:
        from data_paths import get_realtime_dirs
    except ImportError:
        print("Warning: Could not import data_paths module")

def read_specific_realtime_files():
    """
    Read the specific real-time GTFS files from the predefined paths.
    
    Returns:
        dict: Dictionary containing the parsed data from both files
    """
    if not GTFS_RT_AVAILABLE:
        print("Error: gtfs-realtime-bindings not installed. Cannot read real-time data.")
        return None
    
    # Define the specific file paths
    with_changes_path = os.path.join("src", "data", "Real-time_gegevens", 
                                    "real-time_gegevens_met_info_over_spoorveranderingen.bin")
    without_changes_path = os.path.join("src", "data", "Real-time_gegevens", 
                                       "real-time_gegevens_zonder_info_over_spoorveranderingen.bin")
    
    result = {}
    
    # Process each file if it exists
    for file_path, key in [(with_changes_path, "with_changes"), (without_changes_path, "without_changes")]:
        if os.path.exists(file_path):
            try:
                feed = gtfs_realtime_pb2.FeedMessage()
                with open(file_path, 'rb') as f:
                    feed.ParseFromString(f.read())
                
                # Convert to a dictionary structure for easier processing
                entities = []
                for entity in feed.entity:
                    entities.append({
                        "id": entity.id,
                        "vehicle": parse_vehicle(entity.vehicle) if entity.HasField('vehicle') else None,
                        "trip_update": parse_trip_update(entity.trip_update) if entity.HasField('trip_update') else None,
                        "alert": parse_alert(entity.alert) if entity.HasField('alert') else None
                    })
                
                result[key] = {
                    "header": {
                        "version": feed.header.gtfs_realtime_version,
                        "timestamp": feed.header.timestamp
                    },
                    "entities": entities
                }
                
                print(f"Successfully read {file_path}: {len(entities)} entities found")
            except Exception as e:
                print(f"Error reading {file_path}: {str(e)}")
                result[key] = {"error": str(e)}
        else:
            print(f"Warning: {file_path} does not exist")
            result[key] = {"error": "File not found"}
    
    return result

def parse_vehicle(vehicle):
    """Parse vehicle message to dictionary"""
    if not vehicle:
        return None
        
    result = {}
    
    if vehicle.HasField('trip'):
        result["trip"] = {
            "trip_id": vehicle.trip.trip_id,
            "route_id": vehicle.trip.route_id if vehicle.trip.HasField('route_id') else None,
            "direction_id": vehicle.trip.direction_id if vehicle.trip.HasField('direction_id') else None,
            "start_time": vehicle.trip.start_time if vehicle.trip.HasField('start_time') else None,
            "start_date": vehicle.trip.start_date if vehicle.trip.HasField('start_date') else None,
        }
    
    if vehicle.HasField('vehicle'):
        result["vehicle"] = {
            "id": vehicle.vehicle.id,
            "label": vehicle.vehicle.label if vehicle.vehicle.HasField('label') else None,
            "license_plate": vehicle.vehicle.license_plate if vehicle.vehicle.HasField('license_plate') else None
        }
    
    if vehicle.HasField('position'):
        result["position"] = {
            "latitude": vehicle.position.latitude,
            "longitude": vehicle.position.longitude,
            "bearing": vehicle.position.bearing if vehicle.position.HasField('bearing') else None,
            "speed": vehicle.position.speed if vehicle.position.HasField('speed') else None,
        }
    
    if vehicle.HasField('current_stop_sequence'):
        result["current_stop_sequence"] = vehicle.current_stop_sequence
    
    if vehicle.HasField('stop_id'):
        result["stop_id"] = vehicle.stop_id
    
    if vehicle.HasField('current_status'):
        statuses = ["INCOMING_AT", "STOPPED_AT", "IN_TRANSIT_TO"]
        result["current_status"] = statuses[vehicle.current_status] if 0 <= vehicle.current_status < len(statuses) else str(vehicle.current_status)
    
    if vehicle.HasField('timestamp'):
        result["timestamp"] = vehicle.timestamp
    
    return result

def parse_trip_update(trip_update):
    """Parse trip update message to dictionary"""
    if not trip_update:
        return None
        
    result = {}
    
    if trip_update.HasField('trip'):
        result["trip"] = {
            "trip_id": trip_update.trip.trip_id,
            "route_id": trip_update.trip.route_id if trip_update.trip.HasField('route_id') else None,
            "direction_id": trip_update.trip.direction_id if trip_update.trip.HasField('direction_id') else None,
            "start_time": trip_update.trip.start_time if trip_update.trip.HasField('start_time') else None,
            "start_date": trip_update.trip.start_date if trip_update.trip.HasField('start_date') else None,
        }
    
    if trip_update.HasField('vehicle'):
        result["vehicle"] = {
            "id": trip_update.vehicle.id,
            "label": trip_update.vehicle.label if trip_update.vehicle.HasField('label') else None,
            "license_plate": trip_update.vehicle.license_plate if trip_update.vehicle.HasField('license_plate') else None
        }
    
    if trip_update.HasField('timestamp'):
        result["timestamp"] = trip_update.timestamp
    
    result["stop_time_updates"] = []
    for stop_time_update in trip_update.stop_time_update:
        update = {
            "stop_sequence": stop_time_update.stop_sequence if stop_time_update.HasField('stop_sequence') else None,
            "stop_id": stop_time_update.stop_id if stop_time_update.HasField('stop_id') else None,
        }
        
        if stop_time_update.HasField('arrival'):
            update["arrival"] = {
                "delay": stop_time_update.arrival.delay if stop_time_update.arrival.HasField('delay') else None,
                "time": stop_time_update.arrival.time if stop_time_update.arrival.HasField('time') else None,
                "uncertainty": stop_time_update.arrival.uncertainty if stop_time_update.arrival.HasField('uncertainty') else None
            }
        
        if stop_time_update.HasField('departure'):
            update["departure"] = {
                "delay": stop_time_update.departure.delay if stop_time_update.departure.HasField('delay') else None,
                "time": stop_time_update.departure.time if stop_time_update.departure.HasField('time') else None,
                "uncertainty": stop_time_update.departure.uncertainty if stop_time_update.departure.HasField('uncertainty') else None
            }
        
        result["stop_time_updates"].append(update)
    
    return result

def parse_alert(alert):
    """Parse alert message to dictionary"""
    if not alert:
        return None
        
    result = {
        "active_period": [],
        "informed_entity": []
    }
    
    for period in alert.active_period:
        result["active_period"].append({
            "start": period.start if period.HasField('start') else None,
            "end": period.end if period.HasField('end') else None
        })
    
    for entity in alert.informed_entity:
        informed_entity = {
            "agency_id": entity.agency_id if entity.HasField('agency_id') else None,
            "route_id": entity.route_id if entity.HasField('route_id') else None,
            "route_type": entity.route_type if entity.HasField('route_type') else None,
            "stop_id": entity.stop_id if entity.HasField('stop_id') else None,
        }
        
        if entity.HasField('trip'):
            informed_entity["trip"] = {
                "trip_id": entity.trip.trip_id,
                "route_id": entity.trip.route_id if entity.trip.HasField('route_id') else None
            }
            
        result["informed_entity"].append(informed_entity)
    
    if alert.HasField('cause'):
        result["cause"] = alert.cause
    
    if alert.HasField('effect'):
        result["effect"] = alert.effect
    
    if alert.HasField('url') and len(alert.url.translation) > 0:
        result["url"] = alert.url.translation[0].text
    
    if alert.HasField('header_text') and len(alert.header_text.translation) > 0:
        result["header_text"] = alert.header_text.translation[0].text
    
    if alert.HasField('description_text') and len(alert.description_text.translation) > 0:
        result["description_text"] = alert.description_text.translation[0].text
    
    return result

def extract_vehicle_positions(realtime_data):
    """
    Extract vehicle positions from GTFS real-time data for display on a map
    
    Args:
        realtime_data (dict): Real-time data dictionary
        
    Returns:
        list: List of vehicle positions with coordinates and metadata
    """
    positions = []
    
    if not realtime_data:
        return positions
    
    # Process both with and without changes data
    for data_type, data in realtime_data.items():
        if "entities" not in data:
            continue
            
        for entity in data["entities"]:
            if "vehicle" in entity and entity["vehicle"] and "position" in entity["vehicle"]:
                vehicle = entity["vehicle"]
                position = vehicle["position"]
                
                if "latitude" in position and "longitude" in position:
                    vehicle_info = {
                        "id": entity.get("id", "unknown"),
                        "latitude": position["latitude"],
                        "longitude": position["longitude"],
                        "bearing": position.get("bearing"),
                        "speed": position.get("speed"),
                        "status": vehicle.get("current_status"),
                        "timestamp": vehicle.get("timestamp"),
                        "has_platform_change": data_type == "with_changes"
                    }
                    
                    # Add trip information if available
                    if "trip" in vehicle:
                        vehicle_info["trip_id"] = vehicle["trip"].get("trip_id")
                        vehicle_info["route_id"] = vehicle["trip"].get("route_id")
                        
                    # Add vehicle details if available
                    if "vehicle" in vehicle:
                        vehicle_info["vehicle_id"] = vehicle["vehicle"].get("id")
                        vehicle_info["vehicle_label"] = vehicle["vehicle"].get("label")
                        
                    positions.append(vehicle_info)
    
    return positions

def create_sample_files():
    """
    Create sample GTFS real-time Protocol Buffer files in the predefined paths
    """
    if not GTFS_RT_AVAILABLE:
        print("Error: gtfs-realtime-bindings not installed. Cannot create sample files.")
        return False
    
    # Get the realtime directories
    try:
        realtime_dirs = get_realtime_dirs()
        if not realtime_dirs or len(realtime_dirs) < 2:
            print("Error: Could not get real-time directories")
            return False
    except:
        print("Error: Could not get real-time directories")
        return False
        
    # Define the specific file paths
    with_changes_path = os.path.join(realtime_dirs[0], "real-time_gegevens_met_info_over_spoorveranderingen.bin")
    without_changes_path = os.path.join(realtime_dirs[1], "real-time_gegevens_zonder_info_over_spoorveranderingen.bin")
    
    # Create a sample feed with platform changes
    feed_with_changes = gtfs_realtime_pb2.FeedMessage()
    feed_with_changes.header.gtfs_realtime_version = "2.0"
    feed_with_changes.header.incrementality = 0  # FULL_DATASET
    feed_with_changes.header.timestamp = int(datetime.datetime.now().timestamp())
    
    # Add train with platform change
    entity1 = feed_with_changes.entity.add()
    entity1.id = "trip_update_1"
    trip_update1 = entity1.trip_update
    trip_update1.trip.trip_id = "IC516"
    trip_update1.trip.route_id = "IC516"
    
    stop_update1 = trip_update1.stop_time_update.add()
    stop_update1.stop_id = "8814001"  # Brussels South
    stop_update1.arrival.delay = 360  # 6 minutes delay
    stop_update1.departure.delay = 360
    
    # Add vehicle position with platform change
    entity2 = feed_with_changes.entity.add()
    entity2.id = "vehicle_1"
    vehicle2 = entity2.vehicle
    vehicle2.trip.trip_id = "IC516"
    vehicle2.trip.route_id = "IC516"
    vehicle2.vehicle.id = "Train IC516"
    vehicle2.vehicle.label = "IC Brussel - Antwerpen"
    vehicle2.position.latitude = 50.8366
    vehicle2.position.longitude = 4.3353
    vehicle2.position.bearing = 45
    vehicle2.current_status = 1  # STOPPED_AT
    vehicle2.current_stop_sequence = 1
    vehicle2.stop_id = "8814001"
    vehicle2.timestamp = int(datetime.datetime.now().timestamp())
    
    # Create a sample feed without platform changes
    feed_without_changes = gtfs_realtime_pb2.FeedMessage()
    feed_without_changes.header.gtfs_realtime_version = "2.0"
    feed_without_changes.header.incrementality = 0  # FULL_DATASET
    feed_without_changes.header.timestamp = int(datetime.datetime.now().timestamp())
    
    # Add train without platform change
    entity3 = feed_without_changes.entity.add()
    entity3.id = "trip_update_2"
    trip_update3 = entity3.trip_update
    trip_update3.trip.trip_id = "IC714"
    trip_update3.trip.route_id = "IC714"
    
    stop_update3 = trip_update3.stop_time_update.add()
    stop_update3.stop_id = "8891009"  # Gent-Sint-Pieters
    stop_update3.arrival.delay = 180  # 3 minutes delay
    stop_update3.departure.delay = 180
    
    # Add vehicle position without platform change
    entity4 = feed_without_changes.entity.add()
    entity4.id = "vehicle_2"
    vehicle4 = entity4.vehicle
    vehicle4.trip.trip_id = "IC714"
    vehicle4.trip.route_id = "IC714"
    vehicle4.vehicle.id = "Train IC714"
    vehicle4.vehicle.label = "IC Brussel - Gent"
    vehicle4.position.latitude = 51.0356
    vehicle4.position.longitude = 3.7105
    vehicle4.position.bearing = 90
    vehicle4.current_status = 2  # IN_TRANSIT_TO
    vehicle4.current_stop_sequence = 5
    vehicle4.stop_id = "8891009"
    vehicle4.timestamp = int(datetime.datetime.now().timestamp())
    
    # Write the sample files
    try:
        # Ensure parent directories exist
        Path(os.path.dirname(with_changes_path)).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(without_changes_path)).mkdir(parents=True, exist_ok=True)
        
        # Write the files
        with open(with_changes_path, 'wb') as f:
            f.write(feed_with_changes.SerializeToString())
        
        with open(without_changes_path, 'wb') as f:
            f.write(feed_without_changes.SerializeToString())
        
        print(f"Sample GTFS real-time files created at:")
        print(f"  - {with_changes_path}")
        print(f"  - {without_changes_path}")
        return True
    except Exception as e:
        print(f"Error creating sample files: {str(e)}")
        return False

if __name__ == "__main__":
    # When run directly, create sample files and read them
    print("Creating sample GTFS real-time files...")
    create_sample_files()
    
    print("\nReading real-time data from specific files...")
    realtime_data = read_specific_realtime_files()
    
    if realtime_data:
        print("\nData summary:")
        for key, data in realtime_data.items():
            if "error" in data:
                print(f"{key}: Error - {data['error']}")
            else:
                print(f"{key}: {len(data.get('entities', []))} entities")
                
                # Count entities by type
                vehicle_count = sum(1 for entity in data.get('entities', []) if entity.get('vehicle'))
                trip_update_count = sum(1 for entity in data.get('entities', []) if entity.get('trip_update'))
                alert_count = sum(1 for entity in data.get('entities', []) if entity.get('alert'))
                
                print(f"  Vehicles: {vehicle_count}, Trip updates: {trip_update_count}, Alerts: {alert_count}")
