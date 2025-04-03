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
    
    if args.app_only:
        run_webapp()
    elif args.analyze_only:
        run_analysis(force_clean=args.clean)
    else:
        # Run both by default
        overview = run_analysis(force_clean=args.clean)
        if overview is not None:
            run_webapp()
