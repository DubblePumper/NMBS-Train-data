"""
Script to read and display the GTFS real-time data from the specific bin files.
"""

import os
import sys
from google.transit import gtfs_realtime_pb2

def read_and_print_realtime_data():
    """Read and print real-time data from the specified bin files"""
    # Define the file paths
    with_changes_path = os.path.join("src", "data", "Real-time_gegevens", 
                                    "real-time_gegevens_met_info_over_spoorveranderingen.bin")
    without_changes_path = os.path.join("src", "data", "Real-time_gegevens", 
                                       "real-time_gegevens_zonder_info_over_spoorveranderingen.bin")
    
    for file_path, description in [
        (with_changes_path, "With platform changes"),
        (without_changes_path, "Without platform changes")
    ]:
        print(f"\n=== Reading {description} data from {file_path} ===")
        
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            continue
        
        try:
            # Read the GTFS real-time data
            feed = gtfs_realtime_pb2.FeedMessage()
            with open(file_path, 'rb') as f:
                feed.ParseFromString(f.read())
            
            # Print header information
            print(f"GTFS-Realtime version: {feed.header.gtfs_realtime_version}")
            print(f"Timestamp: {feed.header.timestamp}")
            
            # Print all entities
            print(f"\nFound {len(feed.entity)} entities:")
            for i, entity in enumerate(feed.entity):
                print(f"\nEntity {i+1}:")
                print(f"  ID: {entity.id}")
                
                # Print trip update information if present
                if entity.HasField('trip_update'):
                    trip = entity.trip_update.trip
                    print(f"  Trip Update:")
                    print(f"    Trip ID: {trip.trip_id}")
                    if trip.HasField('route_id'):
                        print(f"    Route ID: {trip.route_id}")
                    
                    # Print stop time updates
                    for update in entity.trip_update.stop_time_update:
                        print(f"    Stop ID: {update.stop_id}")
                        if update.HasField('arrival') and update.arrival.HasField('delay'):
                            print(f"      Arrival delay: {update.arrival.delay} seconds")
                        if update.HasField('departure') and update.departure.HasField('delay'):
                            print(f"      Departure delay: {update.departure.delay} seconds")
                
                # Print vehicle position information if present
                if entity.HasField('vehicle'):
                    vehicle = entity.vehicle
                    print(f"  Vehicle Position:")
                    if vehicle.HasField('trip'):
                        print(f"    Trip ID: {vehicle.trip.trip_id}")
                    if vehicle.HasField('vehicle'):
                        print(f"    Vehicle ID: {vehicle.vehicle.id}")
                        if vehicle.vehicle.HasField('label'):
                            print(f"    Label: {vehicle.vehicle.label}")
                    
                    if vehicle.HasField('position'):
                        print(f"    Position: ({vehicle.position.latitude}, {vehicle.position.longitude})")
                        if vehicle.position.HasField('bearing'):
                            print(f"    Bearing: {vehicle.position.bearing}°")
                        if vehicle.position.HasField('speed'):
                            print(f"    Speed: {vehicle.position.speed} m/s")
                    
                    if vehicle.HasField('current_status'):
                        statuses = ["INCOMING_AT", "STOPPED_AT", "IN_TRANSIT_TO"]
                        status = statuses[vehicle.current_status] if 0 <= vehicle.current_status < len(statuses) else str(vehicle.current_status)
                        print(f"    Status: {status}")
                    
                    if vehicle.HasField('stop_id'):
                        print(f"    Stop ID: {vehicle.stop_id}")
                
                # Print alert information if present
                if entity.HasField('alert'):
                    alert = entity.alert
                    print(f"  Alert:")
                    if alert.HasField('header_text') and len(alert.header_text.translation) > 0:
                        print(f"    Header: {alert.header_text.translation[0].text}")
                    if alert.HasField('description_text') and len(alert.description_text.translation) > 0:
                        print(f"    Description: {alert.description_text.translation[0].text}")
        
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")

if __name__ == "__main__":
    # Try to create sample files first
    try:
        # Add app directory to path
        app_dir = os.path.dirname(os.path.abspath(__file__))
        if app_dir not in sys.path:
            sys.path.insert(0, app_dir)
            
        from gtfs_realtime_reader import create_sample_files
        print("Creating sample GTFS real-time files...")
        create_sample_files()
    except Exception as e:
        print(f"Warning: Could not create sample files: {str(e)}")
    
    # Read and print the data
    read_and_print_realtime_data()
