"""
Data paths module for NMBS train data.
This module deals with API configuration instead of local paths.
"""

import logging
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Base API URL from environment variables or default
BASE_URL = os.getenv("NMBS_API_URL", "https://nmbsapi.sanderzijntestjes.be/api/")

def ensure_directories():
    """
    Ensure necessary directories exist for output files.
    No input data directories are needed since we use the API.
    Returns paths dictionary with output directories.
    """
    # Create base directory for outputs only
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    output_dir = os.path.join(current_dir, "reports")
    maps_dir = os.path.join(output_dir, "maps")
    realtime_dir = os.path.join(output_dir, "realtime")
    cache_dir = os.path.join(current_dir, "cache")
    
    # Ensure only output directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(maps_dir, exist_ok=True)
    os.makedirs(realtime_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    
    logger.info(f"Ensured output directories exist: {output_dir}, {maps_dir}, {realtime_dir}, {cache_dir}")
    
    # Return minimal paths dict with only necessary output paths
    return {
        'output_dir': output_dir,
        'MAPS_DIR': maps_dir,
        'api_base_url': BASE_URL,
        'realtime_dir': realtime_dir,
        'planning_dir': output_dir,  # We don't need a separate planning dir since we use the API
        'cache_dir': cache_dir
    }

def get_realtime_dirs():
    """
    Get real-time data directories.
    Creates and returns paths for real-time data.
    """
    paths = ensure_directories()
    realtime_base = paths['realtime_dir']
    
    # Create subdirectories for different types of real-time data
    with_changes_dir = os.path.join(realtime_base, "with_platform_changes")
    without_changes_dir = os.path.join(realtime_base, "without_platform_changes")
    
    # Create the subdirectories
    os.makedirs(with_changes_dir, exist_ok=True)
    os.makedirs(without_changes_dir, exist_ok=True)
    
    logger.info(f"Ensured real-time directories exist: {with_changes_dir}, {without_changes_dir}")
    
    return {
        'base': realtime_base,
        'with_changes': with_changes_dir,
        'without_changes': without_changes_dir
    }

def clean_realtime_dirs():
    """
    Clean up real-time data directories by removing old files.
    """
    try:
        dirs = get_realtime_dirs()
        
        # Clean each directory
        for dir_name, dir_path in dirs.items():
            if os.path.exists(dir_path):
                # Count files before deletion
                file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
                
                # Delete all files in the directory
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                
                logger.info(f"Cleaned {file_count} files from {dir_path}")
            else:
                logger.info(f"Directory does not exist, nothing to clean: {dir_path}")
                
        return True
    except Exception as e:
        logger.error(f"Error cleaning real-time directories: {str(e)}")
        return False

def get_api_config():
    """
    Get API configuration from environment variables.
    
    Returns:
        dict: Dictionary with API configuration
    """
    config = {
        'api_url': BASE_URL,
        'api_port': int(os.getenv('API_PORT', 25580)),
        'api_host': os.getenv('API_HOST', '0.0.0.0'),
        'user_agent': os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0'),
        'cookies_file': os.getenv('COOKIES_FILE', 'data/cookies.json'),
        'nmbs_data_url': os.getenv('NMBS_DATA_URL', '')
    }
    
    logger.info(f"Loaded API configuration: API URL={config['api_url']}, Port={config['api_port']}")
    return config