"""
Main entry point for the NMBS Train Data Analysis application.
This script runs the analysis and launches the Dash web app.
"""

import os
import sys
from pathlib import Path
import subprocess
import argparse
import traceback

# Add the app directory to the path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Check and install required packages
def check_requirements():
    """Check if required packages are installed and install them if missing"""
    try:
        import importlib
        required_packages = [
            "pandas", "matplotlib", "numpy", "dash", "plotly", "folium", 
            "protobuf"
        ]
        
        for package in required_packages:
            try:
                importlib.import_module(package)
            except ImportError:
                print(f"Installing required package: {package}")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                
        # Handle the special case for gtfs-realtime-bindings
        try:
            importlib.import_module("google.transit.gtfs_realtime_pb2")
        except ImportError:
            print("Installing gtfs-realtime-bindings")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "gtfs-realtime-bindings"])
            
        print("All required packages are installed.")
        return True
    except Exception as e:
        print(f"Error checking/installing requirements: {e}")
        return False

from data_paths import ensure_directories, clean_realtime_dirs
from train_data_overview import TrainDataAnalyzer

def run_analysis(force_clean=False):
    """Run the data analysis and generate the overview"""
    try:
        # Ensure directories exist
        paths = ensure_directories()
        
        # Clean realtime directories if requested
        if force_clean:
            print("Cleaning realtime directories...")
            clean_realtime_dirs()
        
        # Create an analyzer with absolute paths
        analyzer = TrainDataAnalyzer(
            planning_dir=paths['planning_dir'],
            realtime_dir=paths['realtime_dir']
        )
        
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
        overview_path = os.path.join(app_dir, "train_data_overview.json")
        analyzer.save_overview(overview, filename=overview_path)
        
        # Generate sample GTFS realtime data if needed
        try:
            print("\nGenerating and reading GTFS real-time data...")
            from gtfs_realtime_reader import create_sample_files, read_specific_realtime_files
            
            # Create sample files if they don't exist
            create_sample_files()
            
            # Read the real-time data from the specific files
            realtime_data = read_specific_realtime_files()
            if realtime_data:
                print("Successfully read GTFS real-time data from specific files")
                
                # Save as JSON for easier inspection
                import json
                realtime_json_path = os.path.join(app_dir, "realtime_data.json")
                with open(realtime_json_path, 'w') as f:
                    json.dump(realtime_data, f, indent=2)
                print(f"Real-time data saved as JSON to {realtime_json_path}")
        except Exception as e:
            print(f"Note: GTFS real-time data processing skipped: {e}")
        
        # Pre-generate a route map for faster loading in the app
        try:
            print("\nPre-generating route map...")
            from map_visualization import visualize_train_routes
            map_path = visualize_train_routes(output_file="default_route_map.html")
            print(f"Default map created at {map_path}")
        except Exception as e:
            print(f"Warning: Could not pre-generate route map: {e}")
        
        print("\nData analysis complete!")
        print(f"Overview saved to {overview_path}")
        
        return overview
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        traceback.print_exc()
        print("\nTrying again after cleaning directories...")
        # If there was an error and force_clean wasn't already true, try again with cleaning
        if not force_clean:
            return run_analysis(force_clean=True)
        else:
            print("Analysis failed even after cleaning directories.")
            return None

def run_webapp():
    """Run the Dash web application"""
    try:
        os.environ["DASH_DARK_MODE"] = "1"  # Set environment variable for dark mode
        app_path = os.path.join(app_dir, "app.py")
        print(f"Starting web application from {app_path}")
        subprocess.run([sys.executable, app_path])
    except Exception as e:
        print(f"Error starting web app: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NMBS Train Data Analysis Tool"
    )
    parser.add_argument(
        "--analyze-only", 
        action="store_true", 
        help="Only run analysis without starting the web app"
    )
    parser.add_argument(
        "--app-only", 
        action="store_true", 
        help="Only start the web app without running analysis"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean realtime directories before running"
    )
    
    args = parser.parse_args()
    
    # Check requirements first
    check_requirements()
    
    if args.app_only:
        run_webapp()
    elif args.analyze_only:
        run_analysis(force_clean=args.clean)
    else:
        # Run both by default
        overview = run_analysis(force_clean=args.clean)
        if overview is not None:
            run_webapp()
