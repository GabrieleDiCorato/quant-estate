"""
Base classes for real estate data connectors.
"""

from sources.connectors.base_scraper import AbstractScraper
from sources.connectors.base_storage import AbstractStorage
from ..exceptions import ScrapingError, StorageError, ValidationError

class AbstractConnector:
    """Base class for real estate data connectors."""
    
    def __init__(self, scraper: AbstractScraper, storage: AbstractStorage):
        """Initialize the connector with a scraper and storage.
        
        Args:
            scraper: Scraper instance
            storage: Storage instance
        """
        self.scraper = scraper
        self.storage = storage
    
    def scrape_and_store(self, start_url: str, max_pages: int | None) -> bool:
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
                return False
            except Exception as e:
                success = False
                raise ScrapingError(f"Unexpected error during scraping: {e}")
        
        return success 