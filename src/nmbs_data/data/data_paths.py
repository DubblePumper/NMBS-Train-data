"""
Module for handling data paths for NMBS train data.
"""

import os
from pathlib import Path
import shutil

def ensure_directories():
    """
    Ensure that all necessary data directories exist.
    Returns a dictionary of path strings.
    """
    # Determine the project root directory
    project_root = Path(__file__).resolve().parents[3]  # Go up 3 levels from this file
    
    # Define standard paths
    data_dir = project_root / "data"
    planning_dir = data_dir / "Planningsgegevens"
    realtime_dir = data_dir / "Real-time_gegevens"
    maps_dir = data_dir / "Maps"  # Added maps directory
    reports_dir = project_root / "reports"
    
    # Create directories if they don't exist
    for directory in [data_dir, planning_dir, realtime_dir, maps_dir, reports_dir]:
        os.makedirs(directory, exist_ok=True)
    
    # Return paths as strings in a dictionary
    return {
        'project_root': str(project_root),
        'data_dir': str(data_dir),
        'planning_dir': str(planning_dir),
        'realtime_dir': str(realtime_dir),
        'maps_dir': str(maps_dir),  # Added maps_dir to the returned dictionary
        'reports_dir': str(reports_dir)
    }

def get_realtime_dirs():
    """
    Get real-time data directories.
    Returns a list of directory paths.
    """
    paths = ensure_directories()
    realtime_base = paths['realtime_dir']
    
    # Define the standard subdirectories for real-time data
    with_changes_dir = os.path.join(realtime_base, "real-time_gegevens_met_info_over_spoorveranderingen")
    without_changes_dir = os.path.join(realtime_base, "real-time_gegevens_zonder_info_over_spoorveranderingen")
    
    # Create subdirectories if they don't exist
    for dir_path in [with_changes_dir, without_changes_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    return [with_changes_dir, without_changes_dir]

def clean_realtime_dirs():
    """
    Clean real-time data directories by removing all files.
    Returns True if successful.
    """
    realtime_dirs = get_realtime_dirs()
    
    for dir_path in realtime_dirs:
        try:
            # Keep the directory but remove its contents
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            print(f"Cleaned directory: {dir_path}")
        except Exception as e:
            print(f"Error cleaning directory {dir_path}: {e}")
            return False
    
    return True