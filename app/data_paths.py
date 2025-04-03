"""
Helper module to standardize paths to data directories across the application.
This ensures consistent path handling regardless of where the script is run from.
"""

import os
from pathlib import Path
import shutil

# Get the application root directory
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)

# Define paths to data directories
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PLANNING_DIR = os.path.join(DATA_DIR, "Planningsgegevens")
REALTIME_DIR = os.path.join(DATA_DIR, "Real-time_gegevens")

# Ensure data directories exist
def ensure_directories():
    """Ensure all required data directories exist"""
    directories = [
        DATA_DIR,
        PLANNING_DIR,
        REALTIME_DIR
    ]
    
    # Create parent directories first
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning when creating directory {directory}: {str(e)}")
    
    # Then create realtime subdirectories
    realtime_subdirs = [
        os.path.join(REALTIME_DIR, "real-time_gegevens_met_info_over_spoorveranderingen"),
        os.path.join(REALTIME_DIR, "real-time_gegevens_zonder_info_over_spoorveranderingen")
    ]
    
    for subdir in realtime_subdirs:
        try:
            # Handle the case where the path might exist but is a file
            if os.path.exists(subdir) and not os.path.isdir(subdir):
                os.remove(subdir)  # Remove the file
                Path(subdir).mkdir(parents=True, exist_ok=True)
            else:
                Path(subdir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning when creating directory {subdir}: {str(e)}")
            # Try an alternative approach if the first method fails
            try:
                os.makedirs(subdir, exist_ok=True)
            except:
                print(f"Could not create directory {subdir} - will continue anyway")
    
    return {
        'data_dir': DATA_DIR,
        'planning_dir': PLANNING_DIR,
        'realtime_dir': REALTIME_DIR
    }

# Function to get absolute paths for realtime directories
def get_realtime_dirs():
    """Get absolute paths to realtime data directories"""
    with_changes = os.path.join(REALTIME_DIR, "real-time_gegevens_met_info_over_spoorveranderingen")
    without_changes = os.path.join(REALTIME_DIR, "real-time_gegevens_zonder_info_over_spoorveranderingen")
    
    # Create directories if they don't exist, using a more robust method
    for dir_path in [with_changes, without_changes]:
        try:
            # Remove the path if it exists but is not a directory
            if os.path.exists(dir_path) and not os.path.isdir(dir_path):
                os.remove(dir_path)
                
            # Create the directory
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: {str(e)}")
    
    return [with_changes, without_changes]

def clean_realtime_dirs():
    """Clean realtime directories by removing and recreating them"""
    with_changes = os.path.join(REALTIME_DIR, "real-time_gegevens_met_info_over_spoorveranderingen")
    without_changes = os.path.join(REALTIME_DIR, "real-time_gegevens_zonder_info_over_spoorveranderingen")
    
    # Remove the directories if they exist
    for dir_path in [with_changes, without_changes]:
        try:
            if os.path.exists(dir_path):
                if os.path.isdir(dir_path):
                    shutil.rmtree(dir_path)
                else:
                    os.remove(dir_path)
        except Exception as e:
            print(f"Warning when removing {dir_path}: {str(e)}")
    
    # Create the directories
    for dir_path in [with_changes, without_changes]:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning when creating {dir_path}: {str(e)}")
    
    return [with_changes, without_changes]

if __name__ == "__main__":
    # If this module is run directly, ensure directories and print their paths
    paths = ensure_directories()
    print("Data directories:")
    for name, path in paths.items():
        print(f"  {name}: {path}")
        print(f"  exists: {os.path.exists(path)}")
    
    # Also print realtime directories
    realtime_dirs = get_realtime_dirs()
    print("\nRealtime directories:")
    for path in realtime_dirs:
        print(f"  {path}")
        print(f"  exists: {os.path.exists(path)}")
