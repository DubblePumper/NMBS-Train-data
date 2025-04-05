#!/usr/bin/env python3
"""
NMBS Train Data Service

This script runs a background service that periodically fetches data from the external NMBS API
and makes it available in memory without downloading files.
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
import threading
import json
import requests
from urllib.parse import urljoin
from dotenv import load_dotenv

# Add the src directory to the path so we can import our packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.getenv("LOG_FILE", "nmbs_service.log"))
    ]
)
logger = logging.getLogger(__name__)

# Get API URL from environment variables or use default
API_URL = os.getenv("NMBS_API_URL", "https://nmbsapi.sanderzijntestjes.be/api/")

class NMBSDataService:
    """Service for periodically fetching NMBS train data from the external API and caching it in memory."""
    
    def __init__(self):
        """Initialize the data service."""
        self.api_url = API_URL
        
        # Set up authentication
        self.user_agent = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0")
        
        # Set up session for requests
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        
        # Initialize running flag
        self._running = False
        
        # Initialize in-memory cache
        self.cache = {
            'realtime_data': None,
            'planning_data': {},
            'last_updated_realtime': None,
            'last_updated_planning': None
        }
        
        logger.info(f"Initialized NMBS Data Service with API URL: {self.api_url}")
    
    def fetch_planning_data(self):
        """Fetch planning data from the external API and store in memory."""
        try:
            # Get list of available planning files
            url = urljoin(self.api_url, "planningdata/files")
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            files = data.get("files", [])
            
            if not files:
                logger.warning("No planning data files available from the API")
                return False
            
            logger.info(f"Found {len(files)} planning files available from the API")
            
            # Fetch each planning file and store in memory
            for filename in files:
                # Remove .txt extension if present for API request
                api_filename = filename
                if api_filename.endswith(".txt"):
                    api_filename = api_filename[:-4]
                
                file_url = urljoin(self.api_url, f"planningdata/{api_filename}")
                logger.info(f"Fetching planning file: {filename}")
                
                file_response = self.session.get(file_url)
                file_response.raise_for_status()
                
                # Store the data in memory
                self.cache['planning_data'][filename] = file_response.json()
                
                logger.info(f"Cached planning file: {filename}")
            
            # Update last updated timestamp
            self.cache['last_updated_planning'] = datetime.now().isoformat()
            
            logger.info(f"Successfully fetched planning data")
            return True
            
        except Exception as e:
            logger.error(f"Error fetching planning data: {str(e)}")
            return False
    
    def fetch_realtime_data(self):
        """Fetch real-time data from the external API and store in memory."""
        try:
            # Get real-time data
            url = urljoin(self.api_url, "realtime/data")
            logger.info(f"Fetching real-time data from {url}")
            
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Store the data in memory
            self.cache['realtime_data'] = data
            self.cache['last_updated_realtime'] = datetime.now().isoformat()
            
            # Process entities with and without platform changes
            with_changes = []
            without_changes = []
            
            # Process the entities to separate those with platform changes
            for entity in data.get('entity', []):
                has_platform_change = False
                
                # Check for platform changes in trip updates
                if 'tripUpdate' in entity and 'stopTimeUpdate' in entity['tripUpdate']:
                    for stop_update in entity['tripUpdate']['stopTimeUpdate']:
                        if 'platform_changed' in stop_update and stop_update['platform_changed']:
                            has_platform_change = True
                            break
                        # Alternative check for platform changes
                        if 'scheduled_platform' in stop_update and 'actual_platform' in stop_update:
                            if stop_update['scheduled_platform'] != stop_update['actual_platform']:
                                has_platform_change = True
                                break
                
                # Add to appropriate list
                if has_platform_change:
                    with_changes.append(entity)
                else:
                    without_changes.append(entity)
            
            # Store the separated data in memory
            self.cache['realtime_with_changes'] = with_changes
            self.cache['realtime_without_changes'] = without_changes
            
            logger.info(f"Cached real-time data: {len(with_changes)} entities with platform changes, "
                        f"{len(without_changes)} entities without platform changes")
            
            return True
            
        except Exception as e:
            logger.error(f"Error fetching real-time data: {str(e)}")
            return False
    
    def get_realtime_data(self):
        """Get the latest real-time data from the cache."""
        return self.cache['realtime_data']
    
    def get_planning_file(self, filename):
        """Get a specific planning file from the cache."""
        return self.cache['planning_data'].get(filename)
    
    def get_planning_files_list(self):
        """Get a list of available planning files from the cache."""
        return list(self.cache['planning_data'].keys())
    
    def get_realtime_with_platform_changes(self):
        """Get real-time data with platform changes from the cache."""
        return self.cache.get('realtime_with_changes', [])
    
    def get_realtime_without_platform_changes(self):
        """Get real-time data without platform changes from the cache."""
        return self.cache.get('realtime_without_changes', [])
    
    def run(self, interval=30, planning_interval=86400):
        """Run the data service, periodically fetching data.
        
        Args:
            interval: Interval in seconds between real-time data fetches
            planning_interval: Interval in seconds between planning data fetches
        """
        self._running = True
        planning_last_fetch = 0
        
        logger.info(f"Starting data service with intervals: real-time={interval}s, planning={planning_interval}s")
        
        # Initial fetches
        self.fetch_planning_data()
        planning_last_fetch = time.time()
        self.fetch_realtime_data()
        
        try:
            while self._running:
                # Check if we need to fetch planning data
                current_time = time.time()
                if current_time - planning_last_fetch >= planning_interval:
                    logger.info("Scheduled planning data fetch...")
                    self.fetch_planning_data()
                    planning_last_fetch = current_time
                
                # Fetch real-time data at the specified interval
                self.fetch_realtime_data()
                
                # Sleep until the next interval
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
            self._running = False
        except Exception as e:
            logger.error(f"Service error: {str(e)}")
            self._running = False
    
    def stop(self):
        """Stop the data service."""
        self._running = False
        logger.info("Service shutting down")
    
    def start_background(self, interval=30, planning_interval=86400):
        """Start the data service in a background thread.
        
        Args:
            interval: Interval in seconds between real-time data fetches
            planning_interval: Interval in seconds between planning data fetches
            
        Returns:
            The background thread running the service
        """
        thread = threading.Thread(
            target=self.run, 
            args=(interval, planning_interval),
            daemon=True
        )
        thread.start()
        
        logger.info(f"Started data service in background thread")
        return thread

# Create a singleton instance for global access
_service_instance = None

def get_service_instance():
    """Get or create the singleton service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = NMBSDataService()
    return _service_instance

def start_data_service(interval=30, planning_interval=86400):
    """Start the data service in the background.
    
    Args:
        interval: Interval in seconds between real-time data fetches
        planning_interval: Interval in seconds between planning data fetches
        
    Returns:
        threading.Thread: The background thread running the service
    """
    service = get_service_instance()
    return service.start_background(interval, planning_interval)

def get_realtime_data():
    """Get the latest real-time data."""
    service = get_service_instance()
    return service.get_realtime_data()

def get_planning_file(filename):
    """Get a specific planning file."""
    service = get_service_instance()
    return service.get_planning_file(filename)

def get_planning_files_list():
    """Get a list of available planning files."""
    service = get_service_instance()
    return service.get_planning_files_list()

def main():
    """Main entry point for the data service."""
    parser = argparse.ArgumentParser(description='NMBS Data Collection Service')
    parser.add_argument('--interval', type=int, default=int(os.getenv('INTERVAL', '30')), 
                      help='Interval in seconds between real-time data fetches (default: 30)')
    parser.add_argument('--planning-interval', type=int, default=int(os.getenv('PLANNING_INTERVAL', '86400')),
                      help='Interval in seconds between planning data fetches (default: 86400 - once per day)')
    args = parser.parse_args()
    
    logger.info(f"Starting NMBS Data Collection Service - {datetime.now().isoformat()}")
    logger.info(f"Real-time data fetch interval: {args.interval} seconds")
    logger.info(f"Planning data fetch interval: {args.planning_interval} seconds")
    
    # Create the service
    service = get_service_instance()
    
    try:
        # Run the service in the main thread
        service.run(interval=args.interval, planning_interval=args.planning_interval)
    except KeyboardInterrupt:
        service.stop()
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service error: {str(e)}")
        raise
    finally:
        logger.info("Service shutting down")

if __name__ == "__main__":
    main()