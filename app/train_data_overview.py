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

class TrainDataAnalyzer:
    def __init__(self, planning_dir="../data/Planningsgegevens", realtime_dir="../data/Real-time_gegevens"):
        self.planning_dir = planning_dir
        self.realtime_dir = realtime_dir
        self.planning_data = None
        self.realtime_data = None
        self.netex_data = None
        
    def load_planning_data(self):
        """Load data from planning files including GTFS ZIP files and Netex XML"""
        planning_files = glob.glob(os.path.join(self.planning_dir, "*"))
        
        print(f"Found {len(planning_files)} planning files")
        
        # Dictionary to store different types of planning data
        self.planning_data = {
            'gtfs': {},
            'netex': {},
            'edifact': {},
            'rawdata': {}  # New category for rawdata_TC.zip
        }
        
        for file_path in planning_files:
            try:
                file_name = os.path.basename(file_path)
                
                if file_path.endswith('.zip') and 'GTFS' in file_path:
                    # Process GTFS ZIP file
                    # Check if file is a valid zip
                    try:
                        with open(file_path, 'rb') as test_f:
                            if test_f.read(4) != b'PK\x03\x04':
                                print(f"Warning: {file_name} has a .zip extension but is not a valid ZIP file")
                                continue
                    except Exception as e:
                        print(f"Error checking ZIP file {file_path}: {str(e)}")
                        continue
                        
                    gtfs_data = self._process_gtfs_zip(file_path)
                    self.planning_data['gtfs'][file_name] = gtfs_data
                    print(f"Successfully loaded GTFS data from: {file_name}")
                    
                elif file_path.endswith('.xml') and 'Netex' in file_path:
                    # Process Netex XML file
                    netex_data = self._process_netex_xml(file_path)
                    self.planning_data['netex'][file_name] = netex_data
                    print(f"Successfully loaded Netex data from: {file_name}")
                    
                elif file_path.endswith('.zip') and 'Edifact' in file_path:
                    # Just note Edifact files for now (specialized parsing would be needed)
                    self.planning_data['edifact'][file_name] = {'file_path': file_path}
                    print(f"Noted Edifact file: {file_name} (not processed)")
                
                elif file_path.endswith('.zip') and 'rawdata' in file_path.lower():
                    # Process raw data ZIP file
                    raw_data = self._process_rawdata_zip(file_path)
                    self.planning_data['rawdata'][file_name] = raw_data
                    print(f"Successfully processed raw data from: {file_name}")
                    
                else:
                    print(f"Unsupported planning file format: {file_path}")
                    
            except Exception as e:
                print(f"Error loading {file_path}: {str(e)}")
        
        return self.planning_data
    
    def _process_gtfs_zip(self, zip_path):
        """Extract and process GTFS data from a ZIP file"""
        gtfs_data = {}
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # List all files in the ZIP
                file_list = zip_ref.namelist()
                
                # Process each CSV file in the GTFS package
                for file_name in file_list:
                    if file_name.endswith('.txt'):
                        try:
                            with zip_ref.open(file_name) as file:
                                # Read the CSV file into a pandas DataFrame
                                df = pd.read_csv(file, delimiter=',')
                                gtfs_data[file_name] = df
                        except Exception as e:
                            print(f"Error processing {file_name} in {zip_path}: {str(e)}")
        except zipfile.BadZipFile:
            print(f"Error: {zip_path} is not a valid ZIP file")
        except Exception as e:
            print(f"Error processing ZIP file {zip_path}: {str(e)}")
        
        return gtfs_data
    
    def _process_rawdata_zip(self, zip_path):
        """Process raw data ZIP file (rawdata_TC.zip)"""
        raw_data = {
            'file_info': {
                'size': os.path.getsize(zip_path),
                'last_modified': datetime.fromtimestamp(os.path.getmtime(zip_path)).strftime('%Y-%m-%d %H:%M:%S')
            },
            'contents': {}
        }
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # List all files in the ZIP
                file_list = zip_ref.namelist()
                raw_data['file_count'] = len(file_list)
                
                # Sample the first few files and their types
                sample_size = min(5, len(file_list))
                for i, file_name in enumerate(file_list[:sample_size]):
                    file_info = zip_ref.getinfo(file_name)
                    raw_data['contents'][file_name] = {
                        'size': file_info.file_size,
                        'compressed_size': file_info.compress_size,
                        'file_type': os.path.splitext(file_name)[1],
                    }
                
                # Add some basic statistics about file types
                extensions = [os.path.splitext(f)[1].lower() for f in file_list]
                extension_counts = {ext: extensions.count(ext) for ext in set(extensions)}
                raw_data['file_types'] = extension_counts
                
        except Exception as e:
            raw_data['error'] = str(e)
            
        return raw_data
    
    def _process_netex_xml(self, xml_path):
        """Process Netex XML file"""
        netex_data = {'summary': {}}
        
        try:
            # Parse the XML file
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Extract namespace from root element
            ns = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
            
            # Count elements of different types
            for key in ['StopPlace', 'ScheduledStopPoint', 'ServiceJourney', 'Line', 'Route']:
                elements = root.findall(f".//ns:{key}", ns)
                netex_data['summary'][key] = len(elements)
            
            # Extract basic structure information
            netex_data['namespaces'] = ns
            netex_data['root_tag'] = root.tag
            netex_data['file_size'] = os.path.getsize(xml_path)
            
        except Exception as e:
            netex_data['error'] = str(e)
            
        return netex_data
    
    def load_realtime_data(self):
        """Load data from real-time files (specific NMBS format)"""
        # Ensure the main real-time directory exists
        if not os.path.exists(self.realtime_dir):
            try:
                os.makedirs(self.realtime_dir, exist_ok=True)
                print(f"Created main real-time directory: {self.realtime_dir}")
            except Exception as e:
                print(f"Error creating main real-time directory {self.realtime_dir}: {str(e)}")
        
        realtime_dirs = [
            os.path.join(self.realtime_dir, "real-time_gegevens_met_info_over_spoorveranderingen"),
            os.path.join(self.realtime_dir, "real-time_gegevens_zonder_info_over_spoorveranderingen")
        ]
        
        self.realtime_data = {
            'with_platform_changes': {},
            'without_platform_changes': {}
        }
        
        # Create sample real-time data if directories are empty
        should_create_samples = True
        created_dirs = []
        
        for i, dir_path in enumerate(realtime_dirs):
            # Create directory if it doesn't exist
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    print(f"Created directory: {dir_path}")
                    created_dirs.append(dir_path)
                    
                    # Create a README file with information
                    readme_path = os.path.join(dir_path, "README.txt")
                    with open(readme_path, 'w') as f:
                        f.write(f"This directory is for NMBS real-time data.\n")
                        f.write(f"Data should be in JSON or XML format.\n")
                        f.write(f"Created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    print(f"Created README file in {dir_path}")
                    
                except Exception as e:
                    print(f"Error creating directory {dir_path}: {str(e)}")
                    continue  # Skip this directory if we can't create it
            
            # Process files in the directory
            realtime_files = glob.glob(os.path.join(dir_path, "*"))
            key = 'with_platform_changes' if i == 0 else 'without_platform_changes'
            
            # Filter out README.txt
            realtime_files = [f for f in realtime_files if not f.endswith('README.txt')]
            
            print(f"Found {len(realtime_files)} real-time files in {key}")
            
            if len(realtime_files) > 0:
                should_create_samples = False
            
            for file_path in realtime_files:
                try:
                    file_name = os.path.basename(file_path)
                    if file_path.endswith('.json'):
                        df = pd.read_json(file_path)
                        self.realtime_data[key][file_name] = df
                        print(f"Successfully loaded: {file_name}")
                    elif file_path.endswith('.xml'):
                        # Process XML real-time data
                        xml_data = self._process_realtime_xml(file_path)
                        self.realtime_data[key][file_name] = xml_data
                        print(f"Successfully loaded XML: {file_name}")
                    else:
                        print(f"Unsupported real-time file format: {file_path}")
                except Exception as e:
                    print(f"Error loading {file_path}: {str(e)}")
        
        # Create sample data if both directories are empty or newly created
        if should_create_samples or created_dirs:
            print("Creating sample real-time data files for demonstration...")
            self._create_sample_realtime_data(realtime_dirs)
        
        return self.realtime_data
    
    def _create_sample_realtime_data(self, realtime_dirs):
        """Create sample real-time data files for demonstration"""
        # Sample data with platform changes
        with_changes_sample = {
            "timestamp": datetime.now().isoformat(),
            "station_updates": [
                {
                    "station_id": "8814001",
                    "station_name": "Brussel-Zuid / Bruxelles-Midi",
                    "departures": [
                        {
                            "train_id": "IC 516",
                            "destination": "Antwerpen-Centraal",
                            "scheduled_time": "08:10",
                            "actual_time": "08:16",
                            "delay": 6,
                            "scheduled_platform": "12",
                            "actual_platform": "14",
                            "platform_changed": True,
                            "status": "Delayed"
                        },
                        {
                            "train_id": "IC 2309",
                            "destination": "Oostende",
                            "scheduled_time": "08:15",
                            "actual_time": "08:15",
                            "delay": 0,
                            "scheduled_platform": "5",
                            "actual_platform": "8",
                            "platform_changed": True,
                            "status": "On time"
                        }
                    ]
                }
            ]
        }
        
        # Sample data without platform changes
        without_changes_sample = {
            "timestamp": datetime.now().isoformat(),
            "station_updates": [
                {
                    "station_id": "8814001",
                    "station_name": "Brussel-Zuid / Bruxelles-Midi",
                    "departures": [
                        {
                            "train_id": "IC 714",
                            "destination": "Gent-Sint-Pieters",
                            "scheduled_time": "08:25",
                            "actual_time": "08:28",
                            "delay": 3,
                            "scheduled_platform": "10",
                            "actual_platform": "10",
                            "platform_changed": False,
                            "status": "Delayed"
                        },
                        {
                            "train_id": "IC 1532",
                            "destination": "Liège-Guillemins",
                            "scheduled_time": "08:30",
                            "actual_time": "08:30",
                            "delay": 0,
                            "scheduled_platform": "3",
                            "actual_platform": "3",
                            "platform_changed": False,
                            "status": "On time"
                        }
                    ]
                }
            ]
        }
        
        try:
            # Make sure the directories exist before trying to write to them
            for dir_path in realtime_dirs:
                os.makedirs(dir_path, exist_ok=True)
            
            # Save sample data to files using fixed paths to ensure they exist
            with_changes_dir = realtime_dirs[0]
            without_changes_dir = realtime_dirs[1]
            
            sample_path_with_changes = os.path.join(with_changes_dir, "sample_data_with_platform_changes.json")
            sample_path_without_changes = os.path.join(without_changes_dir, "sample_data_without_platform_changes.json")
            
            # Write the sample data files
            with open(sample_path_with_changes, 'w') as f:
                json.dump(with_changes_sample, f, indent=2)
            print(f"Created sample data file: {sample_path_with_changes}")
            
            with open(sample_path_without_changes, 'w') as f:
                json.dump(without_changes_sample, f, indent=2)
            print(f"Created sample data file: {sample_path_without_changes}")
            
            # Also load the sample data into the realtime_data dictionary
            try:
                # Convert to DataFrame for analysis
                with_changes_df = pd.DataFrame({"station_updates": [with_changes_sample["station_updates"]]})
                without_changes_df = pd.DataFrame({"station_updates": [without_changes_sample["station_updates"]]})
                
                self.realtime_data['with_platform_changes']["sample_data_with_platform_changes.json"] = with_changes_df
                self.realtime_data['without_platform_changes']["sample_data_without_platform_changes.json"] = without_changes_df
            except Exception as e:
                print(f"Error loading sample data into memory: {str(e)}")
                # Still continue even if loading into memory fails
                
        except Exception as e:
            print(f"Error creating sample data files: {str(e)}")
            # If we can't create the sample files, still continue with the program
    
    def _process_realtime_xml(self, xml_path):
        """Process real-time XML data"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Extract namespace
            ns = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
            
            # Basic information
            return {
                'root_tag': root.tag,
                'namespaces': ns,
                'file_size': os.path.getsize(xml_path)
            }
        except Exception as e:
            return {'error': str(e)}
    
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
        """Count the total number of planning files"""
        count = 0
        for category in self.planning_data.values():
            count += len(category)
        return count
    
    def _generate_gtfs_stats(self):
        """Generate statistics for GTFS data"""
        gtfs_stats = {}
        
        for file_name, gtfs_data in self.planning_data['gtfs'].items():
            file_stats = {
                "tables": {},
                "total_records": 0
            }
            
            for table_name, df in gtfs_data.items():
                if isinstance(df, pd.DataFrame):
                    record_count = len(df)
                    file_stats["tables"][table_name] = {
                        "record_count": record_count,
                        "columns": list(df.columns)
                    }
                    file_stats["total_records"] += record_count
            
            gtfs_stats[file_name] = file_stats
        
        return gtfs_stats
    
    def _generate_netex_stats(self):
        """Generate statistics for Netex data"""
        return {
            filename: data.get('summary', {})
            for filename, data in self.planning_data['netex'].items()
        }
    
    def _generate_rawdata_stats(self):
        """Generate statistics for raw data files"""
        rawdata_stats = {}
        
        for file_name, data in self.planning_data['rawdata'].items():
            rawdata_stats[file_name] = {
                'file_count': data.get('file_count', 0),
                'file_types': data.get('file_types', {}),
                'file_info': data.get('file_info', {})
            }
            
        return rawdata_stats
    
    def _generate_realtime_stats(self):
        """Generate statistics for real-time data"""
        stats = {
            "with_platform_changes": {},
            "without_platform_changes": {}
        }
        
        for category, files in self.realtime_data.items():
            for file_name, data in files.items():
                if isinstance(data, pd.DataFrame):
                    stats[category][file_name] = {
                        "record_count": len(data),
                        "columns": list(data.columns)
                    }
                elif isinstance(data, dict):
                    stats[category][file_name] = {
                        "file_size": data.get('file_size', 0),
                        "format": "XML" if file_name.endswith('.xml') else "Unknown"
                    }
        
        return stats
    
    def visualize_data(self, output_dir="reports"):
        """Create visualizations of the data"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a summary visualization
        self._create_summary_visualization(output_dir)
        
        # Create GTFS visualizations if available
        if 'gtfs' in self.planning_data and self.planning_data['gtfs']:
            self._create_gtfs_visualizations(output_dir)
            
        # Create real-time data visualizations
        self._create_realtime_visualizations(output_dir)
        
        print(f"Visualizations saved to {output_dir}")
    
    def _create_summary_visualization(self, output_dir):
        """Create a summary visualization of all data"""
        plt.figure(figsize=(12, 8))
        
        # Count data sources
        gtfs_count = len(self.planning_data.get('gtfs', {}))
        netex_count = len(self.planning_data.get('netex', {}))
        edifact_count = len(self.planning_data.get('edifact', {}))
        rawdata_count = len(self.planning_data.get('rawdata', {}))
        realtime_with_changes = len(self.realtime_data.get('with_platform_changes', {}))
        realtime_without_changes = len(self.realtime_data.get('without_platform_changes', {}))
        
        # Create bar chart
        labels = ['GTFS', 'Netex', 'Edifact', 'Raw Data', 'RT with\nplatform changes', 'RT without\nplatform changes']
        values = [gtfs_count, netex_count, edifact_count, rawdata_count, realtime_with_changes, realtime_without_changes]
        
        plt.bar(labels, values, color=['blue', 'green', 'red', 'purple', 'orange', 'cyan'])
        plt.title('NMBS Data Sources Overview')
        plt.ylabel('Number of Files')
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Add counts above bars
        for i, v in enumerate(values):
            plt.text(i, v + 0.1, str(v), ha='center')
        
        # Save plot
        plt.savefig(os.path.join(output_dir, "data_sources_overview.png"))
        plt.close()
        
        # Create a pie chart of data distribution
        if sum(values) > 0:
            plt.figure(figsize=(10, 10))
            plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, 
                   colors=['blue', 'green', 'red', 'purple', 'orange', 'cyan'])
            plt.axis('equal')
            plt.title('Distribution of Data Sources')
            plt.savefig(os.path.join(output_dir, "data_distribution_pie.png"))
            plt.close()
    
    def _create_gtfs_visualizations(self, output_dir):
        """Create visualizations for GTFS data"""
        # Create directory for GTFS visualizations
        gtfs_dir = os.path.join(output_dir, "gtfs")
        os.makedirs(gtfs_dir, exist_ok=True)
        
        # Process first GTFS file for visualization
        if self.planning_data['gtfs']:
            first_gtfs = next(iter(self.planning_data['gtfs'].values()))
            
            # Visualize stops if available
            if 'stops.txt' in first_gtfs:
                stops_df = first_gtfs['stops.txt']
                if 'stop_lat' in stops_df.columns and 'stop_lon' in stops_df.columns:
                    plt.figure(figsize=(12, 10))
                    plt.scatter(stops_df['stop_lon'], stops_df['stop_lat'], alpha=0.5)
                    plt.title('NMBS Stations Map')
                    plt.xlabel('Longitude')
                    plt.ylabel('Latitude')
                    plt.grid(True)
                    plt.savefig(os.path.join(gtfs_dir, "stations_map.png"))
                    plt.close()
            
            # Visualize routes if available
            if 'routes.txt' in first_gtfs:
                routes_df = first_gtfs['routes.txt']
                if 'route_type' in routes_df.columns:
                    route_types = routes_df['route_type'].value_counts()
                    plt.figure(figsize=(10, 6))
                    route_types.plot(kind='bar')
                    plt.title('NMBS Route Types')
                    plt.xlabel('Route Type')
                    plt.ylabel('Count')
                    plt.savefig(os.path.join(gtfs_dir, "route_types.png"))
                    plt.close()
    
    def _create_realtime_visualizations(self, output_dir):
        """Create visualizations for real-time data"""
        realtime_dir = os.path.join(output_dir, "realtime")
        os.makedirs(realtime_dir, exist_ok=True)
        
        # Create chart showing stats on platform changes
        try:
            # Count sample files
            with_changes = len(self.realtime_data.get('with_platform_changes', {}))
            without_changes = len(self.realtime_data.get('without_platform_changes', {}))
            
            if with_changes > 0 or without_changes > 0:
                plt.figure(figsize=(10, 6))
                plt.bar(['With Platform Changes', 'Without Platform Changes'], 
                        [with_changes, without_changes],
                        color=['purple', 'cyan'])
                plt.title('Real-time Data Files')
                plt.ylabel('Number of Files')
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                
                # Add counts above bars
                for i, v in enumerate([with_changes, without_changes]):
                    plt.text(i, v + 0.1, str(v), ha='center')
                
                plt.savefig(os.path.join(realtime_dir, "realtime_files.png"))
                plt.close()
                
                # If sample data exists, create a visualization of delays
                for category, files in self.realtime_data.items():
                    for file_name, data in files.items():
                        if isinstance(data, pd.DataFrame) and 'station_updates' in data.columns:
                            try:
                                # Extract delays from the sample data - handle both DataFrame and direct dictionary
                                station_updates = []
                                if isinstance(data, pd.DataFrame) and len(data) > 0:
                                    if isinstance(data['station_updates'].iloc[0], list):
                                        station_updates = data['station_updates'].iloc[0]
                                    else:
                                        station_updates = data['station_updates'].tolist()
                                
                                delays = []
                                train_ids = []
                                
                                for station in station_updates:
                                    for departure in station['departures']:
                                        delays.append(departure['delay'])
                                        train_ids.append(departure['train_id'])
                                
                                if delays:
                                    plt.figure(figsize=(10, 6))
                                    plt.bar(train_ids, delays, color='red' if category == 'with_platform_changes' else 'blue')
                                    plt.title(f'Train Delays ({category.replace("_", " ")})')
                                    plt.ylabel('Delay (minutes)')
                                    plt.xlabel('Train ID')
                                    plt.xticks(rotation=45)
                                    plt.grid(axis='y', linestyle='--', alpha=0.7)
                                    plt.tight_layout()
                                    
                                    plt.savefig(os.path.join(realtime_dir, f"delays_{category}.png"))
                                    plt.close()
                            except Exception as e:
                                print(f"Error creating delay visualization for {file_name}: {str(e)}")
        except Exception as e:
            print(f"Error creating real-time visualizations: {str(e)}")
    
    def save_overview(self, overview, filename="train_data_overview.json"):
        """Save the overview to a JSON file"""
        # Convert any non-serializable objects to strings
        def json_serializable(obj):
            if isinstance(obj, (pd.Series, pd.DataFrame)):
                return obj.to_dict()
            elif isinstance(obj, (datetime, np.datetime64)):
                return str(obj)
            elif isinstance(obj, (np.int64, np.float64)):
                return int(obj) if isinstance(obj, np.int64) else float(obj)
            return str(obj)
        
        # Process the overview to make it JSON serializable
        processed_overview = {}
        for key, value in overview.items():
            if isinstance(value, dict):
                processed_overview[key] = {k: json_serializable(v) for k, v in value.items()}
            else:
                processed_overview[key] = json_serializable(value)
        
        # Add metadata
        processed_overview["metadata"] = {
            "generated_at": str(datetime.now()),
            "planning_dir": self.planning_dir,
            "realtime_dir": self.realtime_dir
        }
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(processed_overview, f, indent=2)
        
        print(f"Overview saved to {filename}")
        
        # Also save a human-readable summary text file
        summary_filename = filename.replace('.json', '_summary.txt')
        with open(summary_filename, 'w') as f:
            f.write(f"NMBS Train Data Overview\n")
            f.write(f"Generated: {datetime.now()}\n\n")
            
            f.write(f"Planning Data:\n")
            f.write(f"  GTFS Files: {overview['planning_data']['gtfs_files']}\n")
            f.write(f"  NeTEx Files: {overview['planning_data']['netex_files']}\n")
            f.write(f"  Edifact Files: {overview['planning_data']['edifact_files']}\n")
            f.write(f"  Raw Data Files: {overview['planning_data'].get('rawdata_files', 0)}\n\n")
            
            f.write(f"Real-time Data:\n")
            f.write(f"  With Platform Changes: {overview['realtime_data']['with_platform_changes']}\n")
            f.write(f"  Without Platform Changes: {overview['realtime_data']['without_platform_changes']}\n\n")
            
            f.write(f"Real-time Data Directories:\n")
            f.write(f"  {os.path.join(self.realtime_dir, 'real-time_gegevens_met_info_over_spoorveranderingen')}\n")
            f.write(f"  {os.path.join(self.realtime_dir, 'real-time_gegevens_zonder_info_over_spoorveranderingen')}\n")
        
        print(f"Summary saved to {summary_filename}")

def main():
    # Create an instance of the analyzer
    analyzer = TrainDataAnalyzer()
    
    # Load both datasets
    print("Loading planning data...")
    analyzer.load_planning_data()
    
    print("\nLoading real-time data...")
    analyzer.load_realtime_data()
    
    # Generate overview
    print("\nGenerating overview...")
    overview = analyzer.generate_overview()
    
    # Create visualizations
    print("\nCreating visualizations...")
    analyzer.visualize_data()
    
    # Save overview to file
    analyzer.save_overview(overview)
    
    print("\nData analysis complete!")
    
    return overview

if __name__ == "__main__":
    main()
