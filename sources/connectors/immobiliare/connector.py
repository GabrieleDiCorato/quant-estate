"""
Immobiliare.it connector implementation.
"""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import List, Dict, Any
import json
import requests
from bs4 import BeautifulSoup

from ..base import BaseConnector, BaseScraper
from ..config import ConfigManager
from .exceptions import InvalidURLError, DataExtractionError
from .models import RealEstate
from .scraper import ImmobiliareScraper
from .storage import FileStorage, MongoDBStorage

class ImmobiliareScraper(BaseScraper):
    """Scraper implementation for immobiliare.it."""
    
    def validate_url(self, url: str) -> None:
        """Validate that the URL is appropriate for immobiliare.it."""
        if not self.base_url in url:
            raise InvalidURLError(f"Given URL must include '{self.base_url}'")
        
        if "mapCenter" in url:
            raise InvalidURLError("Given URL must not include 'mapCenter' as it uses another API to retrieve data")
        
        if "search-list" in url:
            raise InvalidURLError("Given URL must not include 'search-list' as it uses another API to retrieve data")
    
    def extract_data(self, response: requests.Response) -> List[Dict[str, Any]]:
        """Extract JSON data from the response."""
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
            
            if not script_tag:
                raise DataExtractionError("Could not find __NEXT_DATA__ script tag")
                
            json_data = script_tag.text
            data = json.loads(json_data)
            return data["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["results"]
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            raise DataExtractionError(f"Failed to extract JSON data: {e}")
    
    def get_next_page_url(self, current_url: str, page_number: int) -> str:
        """Generate the URL for the next page of results."""
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)
        query_params['pag'] = [str(page_number)]
        
        return urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            urlencode(query_params, doseq=True),
            parsed_url.fragment
        ))

class ImmobiliareConnector(BaseConnector):
    """Connector implementation for immobiliare.it."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the connector with configuration."""
        scraper = ImmobiliareScraper(config_manager.get_connector_config('immobiliare'))
        storage = self._create_storage(config_manager.get_storage_config())
        super().__init__(scraper, storage)
    
    def _create_storage(self, storage_config: Dict[str, Any]):
        """Create storage instance based on configuration."""
        storage_type = storage_config.get('type', 'file')
        settings = storage_config.get('settings', {})
        
        if storage_type == 'file':
            return FileStorage(**settings)
        elif storage_type == 'mongodb':
            return MongoDBStorage(**settings)
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}") 