"""
Data service module for NMBS train data.
This module handles the service for downloading and scraping NMBS train data.
"""

import os
import time
import logging
import threading
import requests
import json
import schedule
from datetime import datetime
from pathlib import Path
import cloudscraper
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class NMBSDataService:
    """Service for collecting NMBS train data."""
    
    def __init__(self, data_dir=None):
        """Initialize the data service.
        
        Args:
            data_dir: Directory to store data files
        """
        # Set default data directory if not provided
        if data_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            data_dir = base_dir / "data"
        
        self.data_dir = Path(data_dir)
        self.cookies_file = os.getenv("COOKIES_FILE", str(self.data_dir / "cookies.json"))
        self.user_agent = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0")
        self.nmbs_data_url = os.getenv("NMBS_DATA_URL", "")
        
        # Ensure data directories exist
        self._ensure_directories()
        
        # Initialize scraper
        self.scraper = None
        
        # Create a lock for thread safety
        self.lock = threading.Lock()
        
        logger.info(f"Initialized NMBS Data Service with data directory: {self.data_dir}")
    
    def _ensure_directories(self):
        """Ensure necessary directories exist."""
        # Main data directory
        self.data_dir.mkdir(exist_ok=True)
        
        # Planning data directory
        planning_dir = self.data_dir / "planning"
        planning_dir.mkdir(exist_ok=True)
        
        # Real-time data directories
        realtime_dir = self.data_dir / "realtime"
        realtime_dir.mkdir(exist_ok=True)
        
        # Subdirectories for different types of real-time data
        realtime_with_changes = realtime_dir / "with_platform_changes"
        realtime_without_changes = realtime_dir / "without_platform_changes"
        realtime_with_changes.mkdir(exist_ok=True)
        realtime_without_changes.mkdir(exist_ok=True)
        
        logger.info(f"Ensured data directories exist")
    
    def _init_scraper(self):
        """Initialize the Cloudflare scraper."""
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True},
            delay=10
        )
        self.scraper.headers.update({'User-Agent': self.user_agent})
        
        # Load cookies if available
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                
                for cookie in cookies:
                    self.scraper.cookies.set(cookie['name'], cookie['value'])
                
                logger.info(f"Loaded cookies from {self.cookies_file}")
            except Exception as e:
                logger.error(f"Error loading cookies: {str(e)}")
    
    def scrape_website(self):
        """Scrape the NMBS website to get the latest data URLs."""
        if not self.nmbs_data_url:
            logger.warning("NMBS_DATA_URL not set in .env file")
            return False
        
        # Initialize scraper if not already done
        if self.scraper is None:
            self._init_scraper()
        
        try:
            # Use a lock to ensure thread safety
            with self.lock:
                logger.info(f"Scraping NMBS data website: {self.nmbs_data_url}")
                
                # Make the request to the NMBS data page
                response = self.scraper.get(self.nmbs_data_url)
                response.raise_for_status()
                
                # Save cookies for future use
                cookie_dir = os.path.dirname(self.cookies_file)
                os.makedirs(cookie_dir, exist_ok=True)
                
                with open(self.cookies_file, 'w') as f:
                    json.dump([
                        {'name': cookie.name, 'value': cookie.value}
                        for cookie in self.scraper.cookies
                    ], f)
                
                logger.info(f"Cookies saved to {self.cookies_file}")
                
                # Process the response to extract data URLs
                # This is a placeholder - the actual extraction would depend on the website structure
                # Here we're just simulating the extraction of data URLs
                
                # Store the extracted URLs
                self.data_urls = {
                    "gtfs": "https://nmbsapi.sanderzijntestjes.be/api/planningdata/gtfs",
                    "realtime": "https://nmbsapi.sanderzijntestjes.be/api/realtime/data"
                }
                
                logger.info(f"Successfully scraped NMBS data website")
                return True
                
        except Exception as e:
            logger.error(f"Error scraping NMBS website: {str(e)}")
            return False
    
    def download_data(self):
        """Download the latest data from the NMBS website."""
        try:
            # Use a lock to ensure thread safety
            with self.lock:
                logger.info("Downloading NMBS data")
                
                # Download planning data (GTFS)
                planning_file = self.data_dir / "planning" / f"gtfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                
                # This is a placeholder - would need real URLs from scraping
                gtfs_url = self.data_urls.get("gtfs") if hasattr(self, "data_urls") else "https://nmbsapi.sanderzijntestjes.be/api/planningdata/gtfs"
                
                # Download the planning data
                self._download_file(gtfs_url, planning_file)
                
                # Download real-time data
                realtime_file = self.data_dir / "realtime" / f"realtime_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                # This is a placeholder - would need real URLs from scraping
                realtime_url = self.data_urls.get("realtime") if hasattr(self, "data_urls") else "https://nmbsapi.sanderzijntestjes.be/api/realtime/data"
                
                # Download the real-time data
                self._download_file(realtime_url, realtime_file)
                
                logger.info(f"Successfully downloaded NMBS data")
                return True
                
        except Exception as e:
            logger.error(f"Error downloading NMBS data: {str(e)}")
            return False
    
    def _download_file(self, url, file_path):
        """Download a file from a URL.
        
        Args:
            url: URL to download from
            file_path: Path to save the file to
        """
        try:
            logger.info(f"Downloading {url} to {file_path}")
            
            # Use the scraper if available, otherwise use requests
            if self.scraper is not None:
                response = self.scraper.get(url)
            else:
                response = requests.get(url)
            
            response.raise_for_status()
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the content to the file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Successfully downloaded {url} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file {url}: {str(e)}")
            return False
    
    def start_background_service(self, interval=30, scrape_interval=86400):
        """Start the data service in the background.
        
        Args:
            interval: Interval in seconds between data downloads
            scrape_interval: Interval in seconds between website scraping
        
        Returns:
            The background thread running the service
        """
        def run_service():
            # Initial scrape and download
            self.scrape_website()
            self.download_data()
            
            # Schedule regular scraping and downloading
            schedule.every(scrape_interval).seconds.do(self.scrape_website)
            schedule.every(interval).seconds.do(self.download_data)
            
            # Run the scheduler
            while True:
                schedule.run_pending()
                time.sleep(1)
        
        # Create and start the background thread
        thread = threading.Thread(target=run_service, daemon=True)
        thread.start()
        
        logger.info(f"Started background service with interval {interval}s and scrape interval {scrape_interval}s")
        return thread