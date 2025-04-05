"""
API client for the NMBS Train Data API.

This module provides direct access to the external NMBS train data API,
using the JSON data directly without saving to files.
"""

import json
import requests
import os
import logging
from urllib.parse import urljoin
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API URL from environment variable or use default
API_URL = os.getenv("NMBS_API_URL", "https://nmbsapi.sanderzijntestjes.be/api/")

class NMBSClient:
    """Client for accessing the NMBS train data API."""
    
    def __init__(self, api_url=API_URL):
        """Initialize the API client.
        
        Args:
            api_url: Base URL for the API
        """
        self.api_url = api_url
        self.user_agent = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0")
        
        # Set up session for requests
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        
        logger.info(f"Initialized NMBS API client with API URL: {self.api_url}")
    
    def get_realtime_data(self):
        """Fetch real-time train data from the API.
        
        Returns:
            dict: The GTFS real-time data
        """
        try:
            url = urljoin(self.api_url, "realtime/data")
            logger.info(f"Fetching real-time data from {url}")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching real-time data: {str(e)}")
            return {"error": str(e)}
    
    def get_planning_files_list(self):
        """Get a list of available planning data files.
        
        Returns:
            list: A list of available file names
        """
        try:
            url = urljoin(self.api_url, "planningdata/files")
            logger.info(f"Fetching planning files list from {url}")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            return data.get("files", [])
        except Exception as e:
            logger.error(f"Error fetching planning files list: {str(e)}")
            return []
    
    def get_planning_file(self, filename):
        """Get a specific planning data file.
        
        Args:
            filename (str): Name of the file to retrieve (with or without extension)
        
        Returns:
            list or dict: The file contents
        """
        try:
            # Remove .txt extension if present for API request
            api_filename = filename
            if api_filename.endswith(".txt"):
                api_filename = api_filename[:-4]
            
            url = urljoin(self.api_url, f"planningdata/{api_filename}")
            logger.info(f"Fetching planning file {filename} from {url}")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching planning file {filename}: {str(e)}")
            return {"error": str(e)}
    
    def force_update(self):
        """Request the API to force an immediate update of its data.
        
        Returns:
            bool: True if successful
        """
        try:
            url = urljoin(self.api_url, "update")
            logger.info(f"Requesting data update from {url}")
            
            response = self.session.post(url)
            response.raise_for_status()
            
            data = response.json()
            return data.get("status") == "success"
        except Exception as e:
            logger.error(f"Error forcing update: {str(e)}")
            return False

# Create a singleton instance for convenience
_client = NMBSClient()

# Module-level convenience functions

def get_realtime_data():
    """
    Get real-time NMBS train data directly from the API.
    
    Returns:
        dict: The GTFS real-time data
    """
    return _client.get_realtime_data()

def get_planning_files_list():
    """
    Get a list of available planning data files directly from the API.
    
    Returns:
        list: A list of available file names
    """
    return _client.get_planning_files_list()

def get_planning_file(filename):
    """
    Get a specific planning data file directly from the API.
    
    Args:
        filename (str): Name of the file to retrieve (with or without extension)
    
    Returns:
        list or dict: The file contents
    """
    return _client.get_planning_file(filename)

def force_update():
    """
    Request the API to force an immediate update of its data.
    
    Returns:
        bool: True if successful
    """
    return _client.force_update()