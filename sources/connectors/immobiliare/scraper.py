"""
Scraper implementation for immobiliare.it.
"""

import re
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import json

from ..base import BaseScraper
from .models import RealEstate
from .exceptions import InvalidURLError, DataExtractionError

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
            results = data["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["results"]
            
            # Process surface data
            for record in results:
                if "realEstate" in record and "properties" in record["realEstate"]:
                    surface = record["realEstate"]["properties"][0].get("surface")
                    if surface:
                        surface_match = re.search(r'(\d+\.?\d*)', surface)
                        if surface_match:
                            record["realEstate"]["properties"][0]["surface_value"] = float(surface_match.group(1))
            
            return results
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            raise DataExtractionError(f"Failed to extract JSON data: {e}")
    
    def get_next_page_url(self, current_url: str, page_number: int) -> str:
        """Generate the URL for the next page of results."""
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
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