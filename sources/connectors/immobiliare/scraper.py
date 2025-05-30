import re
from typing import List, Optional
import pandas as pd

from .connector import ImmobiliareConnector
from .models import RealEstate
from .storage import DataStorage
from .config import config
from .exceptions import DataExtractionError

class ImmobiliareScraper:
    """Scrapes real estate data from immobiliare.it."""
    
    def __init__(
        self,
        url: str,
        get_data_of_following_pages: bool = False,
        max_pages: Optional[int] = None,
        storage_path: Optional[str] = None
    ) -> None:
        """Initialize the scraper with the target URL and options.
        
        Args:
            url: The URL to scrape
            get_data_of_following_pages: Whether to scrape following pages
            max_pages: Maximum number of pages to scrape (None for no limit)
            storage_path: Optional custom storage path
        """
        self.connector = ImmobiliareConnector()
        self.base_url = url
        self.get_data_of_following_pages = get_data_of_following_pages
        self.max_pages = max_pages
        self.storage = DataStorage(storage_path)
        self.real_estates: List[RealEstate] = []
        
        # Start scraping
        self.gather_real_estate_data()
        self.data_frame = pd.DataFrame([estate.to_dict() for estate in self.real_estates])
    
    def __str__(self) -> str:
        return f"Immobiliare scraper - url='{self.base_url}'"
    
    def gather_real_estate_data(self) -> None:
        """Gather real estate data from the target URL and optionally following pages."""
        current_url = self.base_url
        current_page = 1
        
        while True:
            print(f"Getting real estate data of {current_url}")
            response = self.connector.get_page(current_url)
            json_data = self.connector.extract_json_data(response)
            
            if not json_data:
                break
            
            self.real_estates.extend(self._process_json_data(json_data))
            
            if not self.get_data_of_following_pages:
                break
                
            if self.max_pages and current_page >= self.max_pages:
                print(f"Reached maximum page limit of {self.max_pages}")
                break
            
            current_page += 1
            current_url = self.connector.get_next_page_url(self.base_url, current_page)
    
    def _process_json_data(self, json_data: List[dict]) -> List[RealEstate]:
        """Process JSON data into RealEstate objects."""
        real_estates = []
        
        for record in json_data:
            try:
                real_estate = RealEstate.from_dict(record)
                
                # Process surface data if available
                if real_estate.surface_formatted:
                    surface_match = re.search(r'(\d+\.?\d*)', real_estate.surface_formatted)
                    if surface_match:
                        real_estate.surface = float(surface_match.group(1))
                
                real_estates.append(real_estate)
                
            except (KeyError, ValueError) as e:
                print(f"Warning: Failed to process record: {e}")
                continue
        
        return real_estates
    
    def save_data_json(self, filename: Optional[str] = None) -> None:
        """Save the scraped data to a JSON file."""
        self.storage.save_json(self.real_estates, filename)
    
    def save_data_csv(self, filename: Optional[str] = None) -> None:
        """Save the scraped data to a CSV file."""
        self.storage.save_csv(self.real_estates, filename) 