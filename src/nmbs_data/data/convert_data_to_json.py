from google.transit import gtfs_realtime_pb2
from google.protobuf.json_format import MessageToDict
import os
import json
from bs4 import BeautifulSoup
import subprocess
import os.path
import cloudscraper
from dotenv import load_dotenv
import json
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = 'data'
BIN_FILES = []
COOKIES_FILE = os.getenv('COOKIES_FILE', 'data/cookies.json')

# Zoek .bin bestanden in de data folder en submappen
for root, _, files in os.walk(DATA_DIR):
    for file in files:
        if file.endswith('.bin'):
            BIN_FILES.append(os.path.join(root, file))

# Als er geen .bin bestanden gevonden zijn, download ze dan
if not BIN_FILES:
    logger.info("Geen .bin bestanden gevonden. Downloading data van NMBS website...")
    
    # URL van de NMBS open data pagina (uit .env file)
    nmbs_url = os.getenv('NMBS_DATA_URL')
    if not nmbs_url:
        logger.error("NMBS_DATA_URL is niet geconfigureerd in .env file")
        exit(1)
    
    # Maak cookies directory indien nodig
    os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
    
    # Initialiseer cloudflare scraper met custom user agent
    user_agent = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        },
        delay=10
    )
    
    # Probeer eerst cookies te laden als ze bestaan
    cookies = None
    if os.path.exists(COOKIES_FILE):
        try:
            with open(COOKIES_FILE, 'r') as f:
                cookies = json.load(f)
                logger.info("Cookies geladen uit bestand")
                
                # Gebruik cookies voor de scraper
                for cookie in cookies:
                    scraper.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
        except Exception as e:
            logger.warning(f"Fout bij laden van cookies: {str(e)}")
    
    # Download de webpagina met cloudflare bypass
    try:
        logger.info(f"Connectie maken met {nmbs_url}...")
        response = scraper.get(nmbs_url)
        
        # Sla cookies op voor toekomstig gebruik
        cookies_dict = [{'name': c.name, 'value': c.value, 'domain': c.domain} for c in scraper.cookies]
        with open(COOKIES_FILE, 'w') as f:
            json.dump(cookies_dict, f)
        
        if response.status_code == 200:
            logger.info("Succesvol verbonden met NMBS website")
            # Parse de HTML met BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Zoek de real-time data links
            realtime_links = []
            
            # Zoek naar alle links met specifieke tekst die naar real-time data verwijzen
            for link in soup.find_all('a', class_='link flex-items-center marg-bottom-sm-10'):
                span_text = link.find('span')
                if span_text and 'real-time gegevens' in span_text.text:
                    url = link.get('href')
                    filename = f"{span_text.text.strip().replace(' ', '_')}.bin"
                    realtime_links.append((url, filename))
            
            if not realtime_links:
                logger.warning("Geen real-time data links gevonden. Mogelijk is de website structuur veranderd.")
            
            # Maak realtime data directories indien nodig
            realtime_dir = os.path.join(DATA_DIR, 'Real-time_gegevens')
            if not os.path.exists(realtime_dir):
                os.makedirs(realtime_dir)
            
            # Download de real-time data bestanden
            for url, filename in realtime_links:
                output_path = os.path.join(realtime_dir, filename)
                
                logger.info(f"Downloading {filename} van {url}...")
                try:
                    # Download het bestand direct met de cloudscraper
                    data_response = scraper.get(url)
                    if data_response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            f.write(data_response.content)
                        logger.info(f"Succesvol gedownload: {output_path}")
                        BIN_FILES.append(output_path)
                    else:
                        logger.error(f"Fout bij downloaden: HTTP status {data_response.status_code}")
                except Exception as e:
                    logger.error(f"Fout bij downloaden: {str(e)}")
        else:
            logger.error(f"Fout bij ophalen van NMBS website: HTTP status {response.status_code}")
    except Exception as e:
        logger.error(f"Fout bij verbinden met NMBS website: {str(e)}")

# Verwerk elk .bin bestand en zet om naar JSON
for bin_file in BIN_FILES:
    logger.info(f"Verwerken van {bin_file}...")
    try:
        feed = gtfs_realtime_pb2.FeedMessage()
        with open(bin_file, 'rb') as f:
            feed.ParseFromString(f.read())
        feed_dict = MessageToDict(feed)
        
        json_file = bin_file.replace('.bin', '.json')
        with open(json_file, 'w') as f:
            json.dump(feed_dict, f, indent=2)
        
        logger.info(f"JSON bestand opgeslagen: {json_file}")
    except Exception as e:
        logger.error(f"Fout bij verwerken van {bin_file}: {str(e)}")