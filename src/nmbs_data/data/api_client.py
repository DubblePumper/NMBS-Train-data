"""
API client for accessing NMBS train data through API endpoints.
Replaces direct file access with API requests.
"""

import json
import requests
import pandas as pd
from datetime import datetime
import os
import time
import threading
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base API URL
BASE_URL = "https://nmbsapi.sanderzijntestjes.be/api/"

class NMBSApiClient:
    """Client for accessing NMBS train data APIs."""
    
    def __init__(self, base_url=BASE_URL, cache_dir=None):
        """Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            cache_dir: Directory to cache API responses
        """
        self.base_url = base_url
        self.cache_dir = cache_dir
        self.cache_expiry = 300  # Cache expires after 5 minutes
        
        # Create cache directory if specified
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def check_api_health(self):
        """Check the health of the API."""
        try:
            response = requests.get(urljoin(self.base_url, "health"))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API health check failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_ping(self):
        """Simple ping test to check if the API is reachable.
        
        Returns:
            dict: Response with status information
        """
        try:
            response = requests.get(urljoin(self.base_url, "ping"), timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API ping failed: {str(e)}")
            # Return a dict for consistent return type
            return {"status": "error", "message": str(e)}
    
    def _get_cache_path(self, endpoint):
        """Get the cache file path for an endpoint."""
        if not self.cache_dir:
            return None
        
        # Create a safe filename from the endpoint
        filename = endpoint.replace("/", "_").replace("?", "_").replace("&", "_")
        return os.path.join(self.cache_dir, f"{filename}.json")
    
    def _is_cache_valid(self, cache_path):
        """Check if the cache file is valid and not expired."""
        if not os.path.exists(cache_path):
            return False
        
        # Check file modification time
        mod_time = os.path.getmtime(cache_path)
        current_time = time.time()
        return (current_time - mod_time) < self.cache_expiry
    
    def _write_cache(self, cache_path, data):
        """Write data to the cache file."""
        if not self.cache_dir:
            return
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to write to cache {cache_path}: {str(e)}")
    
    def _read_cache(self, cache_path):
        """Read data from the cache file."""
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read from cache {cache_path}: {str(e)}")
            return None
    
    def get(self, endpoint, params=None, use_cache=True):
        """Make a GET request to the API endpoint.
        
        Args:
            endpoint: API endpoint to access
            params: Query parameters
            use_cache: Whether to use cached responses
            
        Returns:
            Response data as dictionary
        """
        # Check cache first if enabled
        cache_path = self._get_cache_path(endpoint)
        if use_cache and cache_path and self._is_cache_valid(cache_path):
            cached_data = self._read_cache(cache_path)
            if cached_data:
                logger.info(f"Using cached data for {endpoint}")
                return cached_data
        
        # Make the API request
        url = urljoin(self.base_url, endpoint)
        try:
            logger.info(f"Requesting {url}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response if applicable
            if cache_path:
                self._write_cache(cache_path, data)
            
            return data
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise
    
    def post(self, endpoint, data=None):
        """Make a POST request to the API endpoint.
        
        Args:
            endpoint: API endpoint to access
            data: Data to send in the request
            
        Returns:
            Response data as dictionary
        """
        url = urljoin(self.base_url, endpoint)
        try:
            logger.info(f"POST request to {url}")
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API POST request failed: {str(e)}")
            raise
    
    def get_paginated(self, endpoint, params=None, use_cache=True):
        """Make a GET request to a paginated API endpoint.
        
        Automatically fetches all pages of results and combines them.
        
        Args:
            endpoint: API endpoint to access
            params: Query parameters
            use_cache: Whether to use cached responses
            
        Returns:
            Combined data from all pages
        """
        # Set up initial parameters if not provided
        if params is None:
            params = {}
        
        # Try to use cache for the combined result first
        cache_key = f"{endpoint}_all_pages"
        cache_path = self._get_cache_path(cache_key)
        
        if use_cache and cache_path and self._is_cache_valid(cache_path):
            cached_data = self._read_cache(cache_path)
            if cached_data:
                logger.info(f"Using cached combined data for {endpoint}")
                return cached_data
                
        # If no cache or cache invalid, fetch all pages
        all_data = []
        current_page = 1
        more_pages = True
        
        logger.info(f"Fetching all pages for {endpoint}")
        
        while more_pages:
            # Add current page to parameters
            page_params = params.copy()
            page_params['page'] = current_page
            
            # Make the API request for this page
            url = urljoin(self.base_url, endpoint)
            try:
                logger.info(f"Requesting {url} (page {current_page})")
                response = requests.get(url, params=page_params)
                response.raise_for_status()
                page_data = response.json()
                
                # Check if data field exists and has content
                if "data" in page_data and page_data["data"]:
                    all_data.extend(page_data["data"])
                    current_page += 1
                    
                    # Check if we've reached the last page
                    if "meta" in page_data and "last_page" in page_data["meta"]:
                        if current_page > page_data["meta"]["last_page"]:
                            more_pages = False
                            logger.info(f"Reached last page ({page_data['meta']['last_page']}) for {endpoint}")
                    elif len(page_data["data"]) == 0:
                        # If no metadata but empty data, assume we're done
                        more_pages = False
                        logger.info(f"Empty page received, assuming end of pagination for {endpoint}")
                else:
                    # No data field or empty data, assume we're done
                    more_pages = False
                    logger.info(f"No data field or empty data, ending pagination for {endpoint}")
                    
            except requests.RequestException as e:
                logger.error(f"API request failed for page {current_page}: {str(e)}")
                more_pages = False  # Stop trying more pages if we hit an error
        
        # Cache the combined results if applicable
        if cache_path:
            self._write_cache(cache_path, all_data)
            
        return all_data
    
    # Planning data methods
    def get_planning_data_overview(self):
        """Get an overview of available planning data."""
        return self.get("planningdata/data")
    
    def get_planning_data_files(self):
        """Get a list of available planning data files."""
        return self.get("planningdata/files")
    
    def get_stops(self, use_cache=True):
        """Get the stops data from all pages of the API.
        
        Args:
            use_cache: Whether to use cached responses
            
        Returns:
            List of all stops from all pages
        """
        # Use the paginated method to get all stops across all pages
        return self.get_paginated("planningdata/stops", use_cache=use_cache)
    
    def get_routes(self, use_cache=True):
        """Get the routes data from all pages."""
        return self.get_paginated("planningdata/routes", use_cache=use_cache)
    
    def get_trips(self, use_cache=True):
        """Get the trips data from all pages."""
        return self.get_paginated("planningdata/trips", use_cache=use_cache)
    
    def get_stop_times(self, use_cache=True):
        """Get the stop times data from all pages."""
        return self.get_paginated("planningdata/stop_times", use_cache=use_cache)
    
    def get_calendar(self, use_cache=True):
        """Get the calendar data from all pages."""
        return self.get_paginated("planningdata/calendar", use_cache=use_cache)
    
    def get_calendar_dates(self, use_cache=True):
        """Get the calendar dates data from all pages."""
        return self.get_paginated("planningdata/calendar_dates", use_cache=use_cache)
    
    def get_agency(self, use_cache=True):
        """Get the agency data from all pages."""
        return self.get_paginated("planningdata/agency", use_cache=use_cache)
    
    def get_translations(self, use_cache=True):
        """Get the translations data from all pages."""
        return self.get_paginated("planningdata/translations", use_cache=use_cache)
    
    def get_planning_file(self, filename):
        """Get specific planning data file contents."""
        return self.get(f"planningdata/{filename}")
    
    # Real-time data methods
    def get_realtime_data(self):
        """Get the latest real-time train data."""
        return self.get("realtime/data", use_cache=False)  # Don't cache real-time data
    
    def update_data(self):
        """Force an immediate update of all data."""
        return self.post("update")
    
    # Helper methods to format API data into DataFrames
    def get_stops_df(self):
        """Get stops data as a pandas DataFrame with cache refreshing."""
        # Force cache refresh for stop data
        stops_data = self.get_stops(use_cache=False)
        return pd.DataFrame(stops_data)
    
    def get_routes_df(self):
        """Get routes data as a pandas DataFrame."""
        routes_data = self.get_routes()
        return pd.DataFrame(routes_data)
    
    def get_trips_df(self):
        """Get trips data as a pandas DataFrame."""
        trips_data = self.get_trips()
        return pd.DataFrame(trips_data)
    
    def get_stop_times_df(self):
        """Get stop times data as a pandas DataFrame."""
        stop_times_data = self.get_stop_times()
        return pd.DataFrame(stop_times_data)
    
    def get_calendar_df(self):
        """Get calendar data as a pandas DataFrame."""
        calendar_data = self.get_calendar()
        return pd.DataFrame(calendar_data)
    
    def get_calendar_dates_df(self):
        """Get calendar dates data as a pandas DataFrame."""
        calendar_dates_data = self.get_calendar_dates()
        return pd.DataFrame(calendar_dates_data)

# Create a singleton instance
api_client = NMBSApiClient(cache_dir=os.path.join(os.path.dirname(__file__), "cache"))

# Module-level functions for easy access to the API

def get_realtime_data():
    """
    Get the latest real-time NMBS train data with track changes.
    
    Returns:
        dict: The GTFS real-time data as a dictionary
    """
    return api_client.get_realtime_data()

def get_planning_files_list():
    """
    Get a list of available planning data files.
    
    Returns:
        list: A list of filenames
    """
    files_response = api_client.get_planning_data_files()
    return files_response.get('files', [])

def get_planning_file(filename):
    """
    Get a specific planning data file.
    
    Args:
        filename (str): The name of the file to get
        
    Returns:
        dict or list: The file contents
    """
    return api_client.get_planning_file(filename)

def force_update():
    """
    Force an immediate update of all data.
    
    Returns:
        bool: True if successful
    """
    try:
        response = api_client.update_data()
        return response.get('status') == 'success'
    except Exception:
        return False

def start_data_service(interval=30, scrape_interval=86400):
    """
    Start the data service in the background. This will:
    1. Do an initial scrape of the website if needed
    2. Download the latest data files
    3. Continue running in the background to update the data periodically
    
    Args:
        interval (int): Interval in seconds between data downloads
        scrape_interval (int): Interval in seconds between website scraping
        
    Returns:
        threading.Thread: A background thread running the service
    """
    from nmbs_data.data.data_service import NMBSDataService
    service = NMBSDataService()
    return service.start_background_service(interval, scrape_interval)