import requests
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Optional, Dict, Any
import json

from .exceptions import InvalidURLError, RequestError, DataExtractionError
from .config import config

class ImmobiliareConnector:
    """Handles all communication with immobiliare.it."""
    
    def __init__(self, headers: Dict[str, str] = None):
        """Initialize the connector with optional custom headers."""
        self.headers = headers or config.headers
    
    def validate_url(self, url: str) -> None:
        """Validate that the URL is appropriate for immobiliare.it."""
        if not config.base_url in url:
            raise InvalidURLError(f"Given URL must include '{config.base_url}'")
        
        if "mapCenter" in url:
            raise InvalidURLError("Given URL must not include 'mapCenter' as it uses another API to retrieve data")
        
        if "search-list" in url:
            raise InvalidURLError("Given URL must not include 'search-list' as it uses another API to retrieve data")
    
    def get_page(self, url: str) -> requests.Response:
        """Get a page from immobiliare.it with proper delay and error handling."""
        self.validate_url(url)
        
        try:
            print(f"Requesting URL: {url}")
            response = requests.get(url, headers=self.headers)
            time.sleep(random.uniform(
                config.request_settings["min_delay"],
                config.request_settings["max_delay"]
            ))
            
            if response.status_code != 200:
                raise RequestError(f"Request failed with status code {response.status_code}")
                
            return response
            
        except requests.RequestException as e:
            raise RequestError(f"Failed to make request: {e}")
    
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
    
    def extract_json_data(self, response: requests.Response) -> Optional[Dict[str, Any]]:
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