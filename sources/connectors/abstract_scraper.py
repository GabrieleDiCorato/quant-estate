import logging
from sources.exceptions import ConfigurationError, ScrapingError
from sources.datamodel.listing_details import ListingDetails

import requests
import random
import time
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class Scraper(ABC):
    """Abstract base class for web scrapers."""

    def __init__(self, config: dict[str, Any]):
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

            # Initialize session for cookie handling
            self.session = requests.Session()

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
            # Add small random delay
            delay = random.uniform(self.min_delay, self.max_delay)
            time.sleep(delay)

            # First visit the homepage to get cookies
            if not hasattr(self, '_initialized'):
                logger.debug("Visiting homepage to initialize session...")
                self.session.get(self.base_url, headers=self.headers)
                self._initialized = True
                time.sleep(delay)  # Wait again before the actual request

            # Make request with session (which maintains cookies)
            response = self.session.get(url, headers=self.headers)

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
    def extract_data(self, response: requests.Response) -> list[ListingDetails]:
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
    def get_page_url(self, url_template: str, page_number: int) -> str:
        """ Generate the URL for the next page.
        Args:
            url_template: Template for the URL
            page_number: Page number to generate the URL for

        Returns:
            str: The generated URL for the next page
        """
        pass

    @abstractmethod
    def _should_continue_scraping(self, page_number: int, response: requests.Response | None) -> bool:
        """Determine if scraping should continue based on the response and page number.

        Args:
            page_number: Current page number
            response: HTTP response from the current page
        """
        pass
