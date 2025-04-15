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

def run_visualization(dark_mode=True, realtime=False, trajectories=False, all_pages=False, no_limit=False):
    """Generate train route map visualization
    
    Args:
        dark_mode: Whether to use dark mode for the map
        realtime: Whether to generate a real-time map with auto-updating
        trajectories: Whether to use the new trajectories API endpoint
        all_pages: Whether to fetch all pages of data (for trajectory endpoint)
        no_limit: Whether to disable the trajectory limit for visualization
    """
    if trajectories:
        from nmbs_data.visualization.map_visualization import create_trajectories_map
        pages_to_fetch = -1 if all_pages else 3  # Fetch all pages if requested, otherwise 3 pages
        max_trajectories = float('inf') if no_limit else 100  # No limit if specified
        output_path = create_trajectories_map(max_trajectories=max_trajectories, light_mode=not dark_mode, pages_to_fetch=pages_to_fetch)
        print(f"Trajectories map generated at: {output_path}")
    elif realtime:
        from nmbs_data.visualization.map_visualization import create_realtime_train_routes_map
        output_path = create_realtime_train_routes_map()
        print(f"Real-time map generated at: {output_path}")
    else:
        from nmbs_data.visualization.map_visualization import visualize_train_routes
        output_path = visualize_train_routes(dark_mode=dark_mode)
        print(f"Map generated at: {output_path}")
    
    return output_path

def run_webapp(use_reloader=True):
    """Run the web application
    
    Args:
        use_reloader: Whether to use Flask's automatic reloader. Set to False when running the full workflow.
    """
    # Import here to avoid loading Dash unnecessarily if not running the webapp
    from nmbs_data.webapp.app import app
    # Run the app with the specified reloader setting
    app.run(debug=True, use_reloader=use_reloader)

def run_all(light_mode=False, realtime=False, trajectories=False):
    """Run analysis, generate visualization, and start the web application"""
    print("=== Running complete NMBS train data workflow ===")
    
    # Step 1: Run the data analysis
    print("\n=== Step 1: Running data analysis ===")
    analysis_result = run_analysis()
    
    # Step 2: Generate visualization
    print("\n=== Step 2: Generating map visualization ===")
    dark_mode = not light_mode
    map_path = run_visualization(dark_mode=dark_mode, realtime=realtime, trajectories=trajectories)
    
    # Step 3: Start the web application
    print("\n=== Step 3: Starting web application ===")
    run_webapp(use_reloader=False)
    
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
    vis_parser.add_argument("--realtime", action="store_true", help="Create a real-time updating map")
    vis_parser.add_argument("--trajectories", action="store_true", help="Use the new trajectories API data")
    vis_parser.add_argument("--all-pages", action="store_true", help="Fetch all pages from the trajectories API")
    vis_parser.add_argument("--no-limit", action="store_true", help="Remove the limit on number of trajectories displayed")
    
    # Web app command
    webapp_parser = subparsers.add_parser("webapp", help="Start the web application")
    
    # All-in-one command (new)
    all_parser = subparsers.add_parser("all", help="Run analysis, generate visualization, and start webapp")
    all_parser.add_argument("--light", action="store_true", help="Use light mode for visualization instead of dark mode")
    all_parser.add_argument("--realtime", action="store_true", help="Use real-time data for visualization")
    all_parser.add_argument("--trajectories", action="store_true", help="Use the new trajectories API data")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Determine which command to run
    if args.command == "analyze":
        run_analysis()
    elif args.command == "visualize":
        dark_mode = not args.light
        all_pages = args.all_pages if hasattr(args, "all_pages") else False
        no_limit = args.no_limit if hasattr(args, "no_limit") else False
        run_visualization(dark_mode=dark_mode, realtime=args.realtime, trajectories=args.trajectories, 
                         all_pages=all_pages, no_limit=no_limit)
    elif args.command == "webapp":
        run_webapp()
    elif args.command == "all":
        light_mode = args.light if hasattr(args, "light") else False
        realtime = args.realtime if hasattr(args, "realtime") else False
        trajectories = args.trajectories if hasattr(args, "trajectories") else False
        run_all(light_mode=light_mode, realtime=realtime, trajectories=trajectories)
    else:
        # Default to running the webapp if no command specified
        print("No command specified, starting web application...")
        run_webapp()

if __name__ == "__main__":
    # Set up proper Python path
    setup_paths()
    
    # Run main function
    main()