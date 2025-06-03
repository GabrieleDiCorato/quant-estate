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

from .exceptions import ScrapingError, StorageError, ValidationError

class BaseStorage(ABC):
    """Abstract base class for data storage implementations."""
    
    @abstractmethod
    def append_data(self, data: List[Dict[str, Any]]) -> bool:
        """Append data to storage.
        
        Args:
            data: List of data items to append
            
        Returns:
            bool: True if data was successfully appended
            
        Raises:
            StorageError: If there's an error storing the data
        """
        pass
    
    @abstractmethod
    def load_data(self) -> List[Any]:
        """Load all data from storage.
        
        Returns:
            List of data items
            
        Raises:
            StorageError: If there's an error loading the data
        """
        pass

class BaseScraper(ABC):
    """Abstract base class for web scrapers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the scraper with configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ConfigurationError: If required configuration keys are missing
        """
        try:
            self.config = config
            self.headers = config['headers']
            self.base_url = config['base_url']
            self.min_delay = config['request_settings']['min_delay']
            self.max_delay = config['request_settings']['max_delay']
        except KeyError as e:
            raise ConfigurationError(f"Missing required configuration key: {e}")
    
    def get_page(self, url: str) -> requests.Response:
        """Get a page with proper delay and error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            requests.Response: The HTTP response
            
        Raises:
            ValidationError: If the URL is invalid
            ScrapingError: If there's an error fetching the page
        """
        self.validate_url(url)
        
        try:
            response = requests.get(url, headers=self.headers)
            time.sleep(random.uniform(self.min_delay, self.max_delay))
            
            if response.status_code != 200:
                raise ScrapingError(f"Request failed with status code {response.status_code}")
                
            return response
            
        except requests.RequestException as e:
            raise ScrapingError(f"Failed to make request: {e}")
    
    @abstractmethod
    def validate_url(self, url: str) -> None:
        """Validate that the URL is appropriate for this scraper.
        
        Args:
            url: URL to validate
            
        Raises:
            ValidationError: If the URL is invalid
        """
        pass
    
    @abstractmethod
    def extract_data(self, response: requests.Response) -> List[Dict[str, Any]]:
        """Extract data from the response.
        
        Args:
            response: HTTP response to extract data from
            
        Returns:
            List of extracted data items
            
        Raises:
            ScrapingError: If there's an error extracting data
        """
        pass
    
    @abstractmethod
    def get_next_page_url(self, current_url: str, page_number: int) -> str:
        """Generate the URL for the next page of results.
        
        Args:
            current_url: Current page URL
            page_number: Next page number
            
        Returns:
            str: URL for the next page
            
        Raises:
            ValidationError: If the generated URL is invalid
        """
        pass

class BaseConnector:
    """Base class for real estate data connectors."""
    
    def __init__(self, scraper: BaseScraper, storage: BaseStorage):
        """Initialize the connector with a scraper and storage.
        
        Args:
            scraper: Scraper instance
            storage: Storage instance
        """
        self.scraper = scraper
        self.storage = storage
    
    def scrape_and_store(self, start_url: str, max_pages: Optional[int] = None) -> bool:
        """Scrape data from the start URL and store it.
        
        Args:
            start_url: The URL to start scraping from
            max_pages: Optional maximum number of pages to scrape
            
        Returns:
            bool: True if scraping and storing was successful
            
        Raises:
            ScrapingError: If there's an error during scraping
            StorageError: If there's an error storing the data
            ValidationError: If the URL is invalid
        """
        current_url = start_url
        page_number = 1
        success = True
        
        while True:
            try:
                # Get and parse the page
                response = self.scraper.get_page(current_url)
                data = self.scraper.extract_data(response)
                
                if not data:
                    break
                
                # Store the data
                if not self.storage.append_data(data):
                    raise StorageError(f"Failed to store data from page {page_number}")
                
                # Check if we've reached the maximum number of pages
                if max_pages and page_number >= max_pages:
                    break
                
                # Get the next page URL
                page_number += 1
                current_url = self.scraper.get_next_page_url(current_url, page_number)
                
            except (ScrapingError, StorageError, ValidationError) as e:
                success = False
                raise
            except Exception as e:
                success = False
                raise ScrapingError(f"Unexpected error during scraping: {e}")
        
        return success 