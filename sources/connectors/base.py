"""
Base classes for real estate data connectors.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import json
import time
import random

class BaseStorage(ABC):
    """Abstract base class for data storage implementations."""
    
    @abstractmethod
    def append_data(self, data: List[Dict[str, Any]]) -> bool:
        """Append data to storage."""
        pass
    
    @abstractmethod
    def load_data(self) -> List[Any]:
        """Load all data from storage."""
        pass

class BaseScraper(ABC):
    """Abstract base class for web scrapers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the scraper with configuration."""
        self.config = config
        self.headers = config['headers']
        self.base_url = config['base_url']
        self.min_delay = config['request_settings']['min_delay']
        self.max_delay = config['request_settings']['max_delay']
    
    def get_page(self, url: str) -> requests.Response:
        """Get a page with proper delay and error handling."""
        self.validate_url(url)
        
        try:
            response = requests.get(url, headers=self.headers)
            time.sleep(random.uniform(self.min_delay, self.max_delay))
            
            if response.status_code != 200:
                raise Exception(f"Request failed with status code {response.status_code}")
                
            return response
            
        except requests.RequestException as e:
            raise Exception(f"Failed to make request: {e}")
    
    @abstractmethod
    def validate_url(self, url: str) -> None:
        """Validate that the URL is appropriate for this scraper."""
        pass
    
    @abstractmethod
    def extract_data(self, response: requests.Response) -> List[Dict[str, Any]]:
        """Extract data from the response."""
        pass
    
    @abstractmethod
    def get_next_page_url(self, current_url: str, page_number: int) -> str:
        """Generate the URL for the next page of results."""
        pass

class BaseConnector:
    """Base class for real estate data connectors."""
    
    def __init__(self, scraper: BaseScraper, storage: BaseStorage):
        """Initialize the connector with a scraper and storage."""
        self.scraper = scraper
        self.storage = storage
    
    def scrape_and_store(self, start_url: str, max_pages: Optional[int] = None) -> bool:
        """Scrape data from the start URL and store it.
        
        Args:
            start_url: The URL to start scraping from
            max_pages: Optional maximum number of pages to scrape
            
        Returns:
            bool: True if scraping and storing was successful
        """
        current_url = start_url
        page_number = 1
        
        while True:
            try:
                # Get and parse the page
                response = self.scraper.get_page(current_url)
                data = self.scraper.extract_data(response)
                
                if not data:
                    print(f"No data found on page {page_number}")
                    break
                
                # Store the data
                if not self.storage.append_data(data):
                    print(f"Failed to store data from page {page_number}")
                    break
                
                print(f"Successfully processed page {page_number}")
                
                # Check if we've reached the maximum number of pages
                if max_pages and page_number >= max_pages:
                    break
                
                # Get the next page URL
                page_number += 1
                current_url = self.scraper.get_next_page_url(current_url, page_number)
                
            except Exception as e:
                print(f"Error processing page {page_number}: {e}")
                break
        
        return True 