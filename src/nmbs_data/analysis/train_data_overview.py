"""
Module for analyzing train data from various sources and generating analytics.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import glob
import json
import csv
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import io
import shutil

# Update imports to use new package structure
from nmbs_data.data.data_paths import ensure_directories, get_realtime_dirs, clean_realtime_dirs
from nmbs_data.data.gtfs_realtime_reader import read_specific_realtime_files, create_sample_files
from nmbs_data.data.api_client import api_client

class TrainDataAnalyzer:
    def __init__(self, planning_dir=None, realtime_dir=None):
        # Use the data paths module to get standard paths if not provided
        paths = ensure_directories()
        self.planning_dir = planning_dir if planning_dir else paths['planning_dir']
        self.realtime_dir = realtime_dir if realtime_dir else paths['realtime_dir']
        self.planning_data = None
        self.realtime_data = None
        self.netex_data = None
        self.api_client = api_client

    def load_planning_data(self):
        """Load planning data from API instead of local files"""
        # Dictionary to store different types of planning data
        self.planning_data = {
            'gtfs': {},
            'netex': {},
            'edifact': {},
            'rawdata': {}
        }
        
        try:
            # Check API health
            health = self.api_client.check_api_health()
            if health.get('status') != 'healthy':
                print(f"Warning: API is not healthy: {health}")
                return self.planning_data
                
            # Get available files
            files_response = self.api_client.get_planning_data_files()
            if not files_response.get('files'):
                print("No planning data files available from API")
                return self.planning_data
                
            print(f"Found {len(files_response['files'])} planning files in API")
            
            # Load GTFS data: stops, routes, trips, stop_times, etc.
            try:
                # Stops data
                stops_df = self.api_client.get_stops_df()
                self.planning_data['gtfs']['stops.txt'] = stops_df
                print(f"Loaded stops data: {len(stops_df)} records")
                
                # Routes data
                routes_df = self.api_client.get_routes_df()
                self.planning_data['gtfs']['routes.txt'] = routes_df
                print(f"Loaded routes data: {len(routes_df)} records")
                
                # Trips data
                trips_df = self.api_client.get_trips_df()
                self.planning_data['gtfs']['trips.txt'] = trips_df
                print(f"Loaded trips data: {len(trips_df)} records")
                
                # Stop times data
                stop_times_df = self.api_client.get_stop_times_df()
                self.planning_data['gtfs']['stop_times.txt'] = stop_times_df
                print(f"Loaded stop_times data: {len(stop_times_df)} records")
                
                # Calendar data
                calendar_df = self.api_client.get_calendar_df()
                self.planning_data['gtfs']['calendar.txt'] = calendar_df
                print(f"Loaded calendar data: {len(calendar_df)} records")
                
                # Calendar dates data
                calendar_dates_df = self.api_client.get_calendar_dates_df()
                self.planning_data['gtfs']['calendar_dates.txt'] = calendar_dates_df
                print(f"Loaded calendar_dates data: {len(calendar_dates_df)} records")
                
                # Combine all GTFS data into a virtual "GTFS package"
                self.planning_data['gtfs']['API_GTFS_Package'] = {
                    'stops.txt': stops_df,
                    'routes.txt': routes_df,
                    'trips.txt': trips_df,
                    'stop_times.txt': stop_times_df,
                    'calendar.txt': calendar_df,
                    'calendar_dates.txt': calendar_dates_df
                }
                print("Successfully loaded GTFS data from API")
                
            except Exception as e:
                print(f"Error loading GTFS data from API: {str(e)}")
            
            # For now, we're not loading NeTEx and Edifact data from API
            # as they might not be available via the API
            
        except Exception as e:
            print(f"Error loading planning data from API: {str(e)}")
        
        return self.planning_data

    def load_realtime_data(self):
        """Load real-time data from the API instead of local files"""
        # Ensure the main real-time directory exists (for cache or output)
        if not os.path.exists(self.realtime_dir):
            try:
                os.makedirs(self.realtime_dir, exist_ok=True)
                print(f"Created main real-time directory: {self.realtime_dir}")
            except Exception as e:
                print(f"Error creating main real-time directory {self.realtime_dir}: {str(e)}")
        
        # Initialize the realtime data structure
        self.realtime_data = {
            'with_platform_changes': {},
            'without_platform_changes': {}
        }
        
        try:
            # Get real-time data from API
            realtime_data = self.api_client.get_realtime_data()
            
            if realtime_data:
                # Process real-time data
                # The data contains both platform changes and no platform changes
                # Sort them based on the presence of platform changes
                
                # Create DataFrame with the realtime data
                self.realtime_data['with_platform_changes']['api_realtime_data'] = pd.DataFrame({
                    'entity': [realtime_data.get('entity', [])]
                })
                
                print("Successfully loaded real-time data from API")
                
                # Process the real-time data to extract platform changes
                self._process_realtime_api_data(realtime_data)
            else:
                print("No real-time data available from API")
                
        except Exception as e:
            print(f"Error loading real-time data from API: {str(e)}")
            
            # If the API fails, try to create sample data instead
            try:
                realtime_dirs = get_realtime_dirs()
                self._create_sample_realtime_data(realtime_dirs)
                print("Created sample real-time data as fallback")
            except Exception as e:
                print(f"Error creating sample data: {str(e)}")
        
        return self.realtime_data
        
    def _process_realtime_api_data(self, realtime_data):
        """Process the real-time data from the API to extract platform changes"""
        try:
            if not realtime_data or 'entity' not in realtime_data:
                return
            
            # Extract entities with platform changes
            entities_with_changes = []
            entities_without_changes = []
            
            for entity in realtime_data.get('entity', []):
                has_platform_change = False
                
                # Check if this entity has platform changes
                if 'tripUpdate' in entity and 'stopTimeUpdate' in entity['tripUpdate']:
                    for stop_update in entity['tripUpdate']['stopTimeUpdate']:
                        # In GTFS-RT, platform changes might be indicated in various ways
                        # We'll look for specific indicators like 'platform_changed' field
                        # or differences between scheduled and actual platforms
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
                    entities_with_changes.append(entity)
                else:
                    entities_without_changes.append(entity)
            
            # Store the sorted entities
            if entities_with_changes:
                self.realtime_data['with_platform_changes']['processed_api_data'] = pd.DataFrame({
                    'entities': [entities_with_changes]
                })
                print(f"Processed {len(entities_with_changes)} entities with platform changes")
            
            if entities_without_changes:
                self.realtime_data['without_platform_changes']['processed_api_data'] = pd.DataFrame({
                    'entities': [entities_without_changes]
                })
                print(f"Processed {len(entities_without_changes)} entities without platform changes")
                
        except Exception as e:
            print(f"Error processing real-time API data: {str(e)}")

    # Keep the original processing methods for backward compatibility and fallback
    def _process_gtfs_zip(self, zip_path):
        """Extract and process GTFS data from a ZIP file"""
        # ... existing code ...
        
    def _process_rawdata_zip(self, zip_path):
        """Process raw data ZIP file (rawdata_TC.zip)"""
        # ... existing code ...
        
    def _process_netex_xml(self, xml_path):
        """Process Netex XML file"""
        # ... existing code ...
        
    def _create_sample_realtime_data(self, realtime_dirs):
        """Create sample real-time data files for demonstration"""
        # ... existing code ...
        
    def _process_realtime_xml(self, xml_path):
        """Process real-time XML data"""
        # ... existing code ...
    
    def generate_overview(self):
        """Generate an overview of planning and real-time data"""
        if self.planning_data is None:
            self.load_planning_data()
        
        if self.realtime_data is None:
            self.load_realtime_data()
        
        overview = {
            "planning_data": {
                "total_files": self._count_planning_files(),
                "gtfs_files": len(self.planning_data.get('gtfs', {})),
                "netex_files": len(self.planning_data.get('netex', {})),
                "edifact_files": len(self.planning_data.get('edifact', {})),
                "rawdata_files": len(self.planning_data.get('rawdata', {}))
            },
            "realtime_data": {
                "with_platform_changes": len(self.realtime_data.get('with_platform_changes', {})),
                "without_platform_changes": len(self.realtime_data.get('without_platform_changes', {}))
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "planning_dir": self.planning_dir,
                "realtime_dir": self.realtime_dir,
                "data_source": "API" if self.api_client else "Local Files"
            }
        }
        
        # Add GTFS statistics if available
        if 'gtfs' in self.planning_data and self.planning_data['gtfs']:
            overview["gtfs_stats"] = self._generate_gtfs_stats()
        
        # Add Netex statistics if available
        if 'netex' in self.planning_data and self.planning_data['netex']:
            overview["netex_stats"] = self._generate_netex_stats()
        
        # Add raw data statistics if available
        if 'rawdata' in self.planning_data and self.planning_data['rawdata']:
            overview["rawdata_stats"] = self._generate_rawdata_stats()
        
        # Add real-time statistics
        overview["realtime_stats"] = self._generate_realtime_stats()
        
        return overview

    def _count_planning_files(self):
        """Count the number of planning files available"""
        # When using the API, we count the number of GTFS files loaded
        if hasattr(self, 'planning_data') and self.planning_data:
            return sum(len(category) for category in self.planning_data.values())
        return 0
            
    def _generate_gtfs_stats(self):
        """Generate statistics for GTFS data"""
        stats = {}
        
        # When using API data, we can still generate statistics
        if 'gtfs' in self.planning_data and self.planning_data['gtfs']:
            try:
                # Get the stops data
                if 'stops.txt' in self.planning_data['gtfs']:
                    stops_df = self.planning_data['gtfs']['stops.txt']
                    stats['stops_count'] = len(stops_df)
                
                # Get the routes data
                if 'routes.txt' in self.planning_data['gtfs']:
                    routes_df = self.planning_data['gtfs']['routes.txt']
                    stats['routes_count'] = len(routes_df)
                    
                    # Count routes by type if route_type column exists
                    if 'route_type' in routes_df.columns:
                        route_types = routes_df['route_type'].value_counts().to_dict()
                        stats['routes_by_type'] = route_types
                
                # Get the trips data
                if 'trips.txt' in self.planning_data['gtfs']:
                    trips_df = self.planning_data['gtfs']['trips.txt']
                    stats['trips_count'] = len(trips_df)
                
                # Get the stop_times data
                if 'stop_times.txt' in self.planning_data['gtfs']:
                    stop_times_df = self.planning_data['gtfs']['stop_times.txt']
                    stats['stop_times_count'] = len(stop_times_df)
                
            except Exception as e:
                print(f"Error generating GTFS statistics: {str(e)}")
                stats['error'] = str(e)
        
        return stats
    
    def _generate_netex_stats(self):
        """Generate statistics for NeTEx data"""
        # When using API, NeTEx data might not be available
        return {"api_available": False}
    
    def _generate_rawdata_stats(self):
        """Generate statistics for raw data"""
        # When using API, raw data might not be available
        return {"api_available": False}
    
    def _generate_realtime_stats(self):
        """Generate statistics for real-time data"""
        stats = {}
        
        if not self.realtime_data:
            return {"error": "No real-time data available"}
        
        try:
            # Count entities with platform changes
            with_changes_count = 0
            if 'with_platform_changes' in self.realtime_data:
                with_platform_changes = self.realtime_data['with_platform_changes']
                
                if 'processed_api_data' in with_platform_changes:
                    if 'entities' in with_platform_changes['processed_api_data'].columns:
                        with_changes_count = len(with_platform_changes['processed_api_data']['entities'].iloc[0])
                
            stats['with_platform_changes_count'] = with_changes_count
            
            # Count entities without platform changes
            without_changes_count = 0
            if 'without_platform_changes' in self.realtime_data:
                without_platform_changes = self.realtime_data['without_platform_changes']
                
                if 'processed_api_data' in without_platform_changes:
                    if 'entities' in without_platform_changes['processed_api_data'].columns:
                        without_changes_count = len(without_platform_changes['processed_api_data']['entities'].iloc[0])
            
            stats['without_platform_changes_count'] = without_changes_count
            
            # Calculate percentages
            total_entities = with_changes_count + without_changes_count
            if total_entities > 0:
                stats['with_platform_changes_percent'] = (with_changes_count / total_entities) * 100
                stats['without_platform_changes_percent'] = (without_changes_count / total_entities) * 100
            else:
                stats['with_platform_changes_percent'] = 0
                stats['without_platform_changes_percent'] = 0
            
            # Add timestamp
            stats['generated_at'] = datetime.now().isoformat()
            
        except Exception as e:
            print(f"Error generating real-time statistics: {str(e)}")
            stats['error'] = str(e)
        
        return stats

def main():
    """Main function to run train data analysis."""
    print("Starting train data analysis...")
    
    # Create analyzer
    analyzer = TrainDataAnalyzer()
    
    # Load planning data
    print("\nLoading planning data...")
    analyzer.load_planning_data()
    
    # Load real-time data
    print("\nLoading real-time data...")
    analyzer.load_realtime_data()
    
    # Generate overview
    print("\nGenerating data overview...")
    overview = analyzer.generate_overview()
    
    # Create output directories if they don't exist
    paths = ensure_directories()
    output_dir = paths['output_dir']
    
    # Save overview as JSON
    print("\nSaving overview to JSON...")
    overview_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "train_data_overview.json")
    with open(overview_path, 'w') as f:
        json.dump(overview, f, indent=2)
    
    # Create a summary text file
    print("\nCreating summary text file...")
    summary_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "train_data_overview_summary.txt")
    with open(summary_path, 'w') as f:
        f.write("NMBS Train Data Overview\n")
        f.write("======================\n\n")
        f.write(f"Generated at: {overview['metadata']['generated_at']}\n\n")
        
        f.write("Planning Data:\n")
        f.write(f"  - Total files: {overview['planning_data']['total_files']}\n")
        f.write(f"  - GTFS files: {overview['planning_data']['gtfs_files']}\n")
        f.write(f"  - NeTEx files: {overview['planning_data']['netex_files']}\n")
        f.write(f"  - EDIFACT files: {overview['planning_data']['edifact_files']}\n")
        f.write(f"  - Raw data files: {overview['planning_data']['rawdata_files']}\n\n")
        
        f.write("Real-time Data:\n")
        f.write(f"  - With platform changes: {overview['realtime_data']['with_platform_changes']}\n")
        f.write(f"  - Without platform changes: {overview['realtime_data']['without_platform_changes']}\n\n")
        
        # Add GTFS statistics if available
        if 'gtfs_stats' in overview:
            f.write("GTFS Statistics:\n")
            for key, value in overview['gtfs_stats'].items():
                f.write(f"  - {key}: {value}\n")
            f.write("\n")
        
        # Add real-time statistics if available
        if 'realtime_stats' in overview:
            f.write("Real-time Statistics:\n")
            for key, value in overview['realtime_stats'].items():
                if key != 'error' and key != 'generated_at':
                    f.write(f"  - {key}: {value}\n")
            f.write("\n")
    
    print(f"\nAnalysis complete. Overview saved to {overview_path}")
    print(f"Summary saved to {summary_path}")
    
    # Return the overview as a result
    return overview

if __name__ == "__main__":
    main()