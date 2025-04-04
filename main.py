#!/usr/bin/env python3
"""
NMBS Train Data Analysis and Visualization Tool
Main entry point for running the application
"""

import argparse
import os
import sys
from pathlib import Path

def setup_paths():
    """Set up Python path to include the src directory"""
    project_root = Path(__file__).resolve().parent
    src_path = project_root / "src"
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

def run_analysis():
    """Run the data analysis process standalone"""
    from nmbs_data.analysis.train_data_overview import main as analysis_main
    return analysis_main()

def run_visualization(dark_mode=True):
    """Generate train route map visualization"""
    from nmbs_data.visualization.map_visualization import visualize_train_routes
    output_path = visualize_train_routes(dark_mode=dark_mode)
    print(f"Map generated at: {output_path}")
    return output_path

def run_webapp():
    """Run the web application"""
    # Import here to avoid loading Dash unnecessarily if not running the webapp
    from nmbs_data.webapp.app import app
    # Do not edit this
    app.run(debug=True)

def run_all(light_mode=False):
    """Run analysis, generate visualization, and start the web application"""
    print("=== Running complete NMBS train data workflow ===")
    
    # Step 1: Run the data analysis
    print("\n=== Step 1: Running data analysis ===")
    analysis_result = run_analysis()
    
    # Step 2: Generate visualization
    print("\n=== Step 2: Generating map visualization ===")
    dark_mode = not light_mode
    map_path = run_visualization(dark_mode=dark_mode)
    
    # Step 3: Start the web application
    print("\n=== Step 3: Starting web application ===")
    run_webapp()
    
    return {
        "analysis_complete": True,
        "visualization_path": map_path,
        "webapp_started": True
    }

def main():
    """Main entry point with command-line argument parsing"""
    parser = argparse.ArgumentParser(description="NMBS Train Data Analysis and Visualization Tool")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Analysis command
    analysis_parser = subparsers.add_parser("analyze", help="Run data analysis without starting webapp")
    
    # Visualization command
    vis_parser = subparsers.add_parser("visualize", help="Generate train route map visualization")
    vis_parser.add_argument("--light", action="store_true", help="Use light mode instead of dark mode")
    
    # Web app command
    webapp_parser = subparsers.add_parser("webapp", help="Start the web application")
    
    # All-in-one command (new)
    all_parser = subparsers.add_parser("all", help="Run analysis, generate visualization, and start webapp")
    all_parser.add_argument("--light", action="store_true", help="Use light mode for visualization instead of dark mode")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Determine which command to run
    if args.command == "analyze":
        run_analysis()
    elif args.command == "visualize":
        dark_mode = not args.light
        run_visualization(dark_mode=dark_mode)
    elif args.command == "webapp":
        run_webapp()
    elif args.command == "all":
        light_mode = args.light if hasattr(args, "light") else False
        run_all(light_mode=light_mode)
    else:
        # Default to running the webapp if no command specified
        print("No command specified, starting web application...")
        run_webapp()

if __name__ == "__main__":
    # Set up proper Python path
    setup_paths()
    
    # Run main function
    main()