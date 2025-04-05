"""
Data paths module for NMBS train data.
This module deals with API configuration instead of local paths.
"""

import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base API URL
BASE_URL = "https://nmbsapi.sanderzijntestjes.be/api/"

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
    
    # Ensure only output directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(maps_dir, exist_ok=True)
    
    logger.info(f"Ensured output directories exist: {output_dir}, {maps_dir}")
    
    # Return minimal paths dict with only necessary output paths
    return {
        'output_dir': output_dir,
        'MAPS_DIR': maps_dir,
        'api_base_url': BASE_URL
    }