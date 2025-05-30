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
        self.failed_pages: List[int] = []
        
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
            print(f"\nProcessing page {current_page}")
            try:
                # Get and process the page
                response = self.connector.get_page(current_url)
                json_data = self.connector.extract_json_data(response)
                
                if not json_data:
                    print(f"No data found on page {current_page}")
                    break
                
                # Process the data
                page_estates = self._process_json_data(json_data)
                self.real_estates.extend(page_estates)
                
                # Append the page data to storage
                if not self._append_page_data(json_data):
                    self.failed_pages.append(current_page)
                    print(f"Warning: Failed to append data for page {current_page}")
                
                if not self.get_data_of_following_pages:
                    break
                    
                if self.max_pages and current_page >= self.max_pages:
                    print(f"Reached maximum page limit of {self.max_pages}")
                    break
                
                current_page += 1
                current_url = self.connector.get_next_page_url(self.base_url, current_page)
                
            except Exception as e:
                print(f"Error processing page {current_page}: {e}")
                self.failed_pages.append(current_page)
                break
    
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
    
    def _append_page_data(self, data: List[dict]) -> bool:
        """Append data for a single page to storage.
        
        Args:
            data: The JSON data to append
            
        Returns:
            bool: True if append was successful, False otherwise
        """
        # Try to append as JSON first
        json_success = self.storage.append_json(data)
        
        # Try to append as CSV as well
        csv_success = self.storage.append_csv(data)
        
        return json_success or csv_success
    
    def get_failed_pages(self) -> List[int]:
        """Get the list of pages that failed to save."""
        return self.failed_pages 