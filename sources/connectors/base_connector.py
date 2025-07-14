"""
Base classes for real estate data connectors.
"""

from requests import Response

from sources.logging_utils.logging_mixin import LoggingMixin
from sources.connectors.base_scraper import AbstractScraper
from sources.connectors.base_storage import AbstractStorage
from ..exceptions import ScrapingError, StorageError, ValidationError
from sources.datamodel.real_estate_listing import RealEstateListing

class AbstractConnector(LoggingMixin):
    """Base class for real estate data connectors."""

    def __init__(self, scraper: AbstractScraper, storage: AbstractStorage) -> None:
        """Initialize the connector with a scraper and storage.
        
        Args:
            scraper: Scraper instance
            storage: Storage instance
            
        Raises:
            TypeError: If scraper or storage are not of the correct type
            ValueError: If scraper or storage are None
        """
        super().__init__()

        if scraper is None:
            raise ValueError("Scraper cannot be None")
        if not isinstance(scraper, AbstractScraper):
            raise TypeError(f"Scraper must be an instance of AbstractScraper, got {type(scraper)}")

        if storage is None:
            raise ValueError("Storage cannot be None")
        if not isinstance(storage, AbstractStorage):
            raise TypeError(f"Storage must be an instance of AbstractStorage, got {type(storage)}")

        self.scraper: AbstractScraper = scraper
        self.storage: AbstractStorage = storage

        self.logger.info("AbstractConnector initialized successfully")

    def scrape_and_store(self, url_template: str) -> bool:
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
            TypeError: If arguments are not of the correct type
            ValueError: If arguments are invalid
        """
        # Validate input parameters
        # Validate start_url
        if not isinstance(url_template, str):
            raise TypeError(f"start_url must be a string, got {type(url_template)}")

        if not url_template or not url_template.strip():
            raise ValueError("start_url cannot be empty or whitespace")

        page_number: int = 1
        success: bool = True
        response: Response | None = None

        while self.scraper._should_continue_scraping(page_number, response):
            try:
                # Get and parse the page
                current_url: str = self.scraper.get_page_url(url_template, page_number)
                response = self.scraper.get_page(current_url)
                data: list[RealEstateListing] = self.scraper.extract_data(response)

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

            except (ScrapingError, StorageError, ValidationError) as e:
                return False
            except Exception as e:
                success = False
                raise ScrapingError(f"Unexpected error during scraping: {e}")

        return success 
