"""
Immobiliare.it connector implementation.
"""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import List, Dict, Any
import json
import requests
from bs4 import BeautifulSoup

from ..base import BaseConnector, BaseScraper
from ...config import ConfigManager
from .exceptions import InvalidURLError, DataExtractionError
from .models import RealEstate
from .scraper import ImmobiliareScraper
from .storage import FileStorage, MongoDBStorage
from ...utils.logging import get_logger, setup_logging

# Set up logging
logger = get_logger("quant_estate.connector.immobiliare")

class ImmobiliareScraper(BaseScraper):
    """Scraper implementation for immobiliare.it."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the scraper with configuration."""
        super().__init__(config)
        self.logger = get_logger("quant_estate.scraper.immobiliare")
        self.logger.info("Initialized ImmobiliareScraper with base URL: %s", self.base_url)
    
    def validate_url(self, url: str) -> None:
        """Validate that the URL is appropriate for immobiliare.it."""
        self.logger.debug("Validating URL: %s", url)
        if not self.base_url in url:
            self.logger.error("Invalid URL: missing base URL %s", self.base_url)
            raise InvalidURLError(f"Given URL must include '{self.base_url}'")
        
        if "mapCenter" in url:
            self.logger.error("Invalid URL: contains 'mapCenter' which uses a different API")
            raise InvalidURLError("Given URL must not include 'mapCenter' as it uses another API to retrieve data")
        
        if "search-list" in url:
            self.logger.error("Invalid URL: contains 'search-list' which uses a different API")
            raise InvalidURLError("Given URL must not include 'search-list' as it uses another API to retrieve data")
        self.logger.debug("URL validation successful")
    
    def extract_data(self, response: requests.Response) -> List[Dict[str, Any]]:
        """Extract JSON data from the response."""
        self.logger.debug("Extracting data from response (status code: %d)", response.status_code)
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
            
            if not script_tag:
                self.logger.error("Failed to find __NEXT_DATA__ script tag in response")
                raise DataExtractionError("Could not find __NEXT_DATA__ script tag")
                
            json_data = script_tag.text
            data = json.loads(json_data)
            results = data["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["results"]
            self.logger.info("Successfully extracted %d real estate listings", len(results))
            return results
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to extract JSON data: %s", str(e), exc_info=True)
            raise DataExtractionError(f"Failed to extract JSON data: {e}")
    
    def get_next_page_url(self, current_url: str, page_number: int) -> str:
        """Generate the URL for the next page of results."""
        self.logger.debug("Generating URL for page %d", page_number)
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)
        query_params['pag'] = [str(page_number)]
        
        next_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            urlencode(query_params, doseq=True),
            parsed_url.fragment
        ))
        self.logger.debug("Generated next page URL: %s", next_url)
        return next_url

class ImmobiliareConnector(BaseConnector):
    """Connector implementation for immobiliare.it."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the connector with configuration."""
        logger.info("Initializing ImmobiliareConnector")
        
        # Set up project-wide logging
        setup_logging(config_manager.get_logging_config())
        
        # Initialize components
        scraper = ImmobiliareScraper(config_manager.get_connector_config('immobiliare'))
        storage = self._create_storage(config_manager.get_storage_config('immobiliare'))
        super().__init__(scraper, storage)
        logger.info("ImmobiliareConnector initialized successfully with %s storage", 
                   storage.__class__.__name__)
    
    def _create_storage(self, storage_config: Dict[str, Any]):
        """Create storage instance based on configuration."""
        logger.debug("Creating storage with config: %s", storage_config)
        storage_type = storage_config['type']
        settings = storage_config['settings']
        
        if storage_type == 'file':
            storage = FileStorage(
                base_path=settings['base_path'],
                save_json=settings['save_json']
            )
            logger.info("Created FileStorage at %s", storage.base_path)
            return storage
        elif storage_type == 'mongodb':
            storage = MongoDBStorage(
                connection_string=settings['connection_string'],
                database=settings['database'],
                collection=settings['collection']
            )
            logger.info("Created MongoDBStorage for %s.%s", 
                       storage.config['database'], 
                       storage.config['collection'])
            return storage
        else:
            logger.error("Unsupported storage type: %s", storage_type)
            raise ValueError(f"Unsupported storage type: {storage_type}")
    
    def scrape_and_store(self, start_url: str, max_pages: int = None) -> bool:
        """Scrape data from the given URL and store it."""
        logger.info("Starting scraping from %s (max pages: %s)", 
                   start_url, 
                   str(max_pages) if max_pages else "unlimited")
        try:
            result = super().scrape_and_store(start_url, max_pages)
            logger.info("Scraping completed successfully")
            return result
        except Exception as e:
            logger.error("Error during scraping: %s", str(e), exc_info=True)
            raise 