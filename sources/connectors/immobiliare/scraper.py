"""
Scraper implementation for immobiliare.it.
"""

import re
import time
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..base import BaseScraper
from ..exceptions import (
    ScrapingError, ValidationError, ConfigurationError,
    InvalidURLError, DataExtractionError, RequestError
)
from .models import RealEstate
from ...logging.logging import get_class_logger

# List of common User-Agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
]

class ImmobiliareScraper(BaseScraper):
    """Scraper implementation for immobiliare.it."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the scraper with configuration.
        
        Args:
            config: Configuration dictionary containing scraper settings
            
        Raises:
            ConfigurationError: If required configuration keys are missing
        """
        super().__init__(config)
        self.logger = get_class_logger(self.__class__)
        
        # Set up session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[403, 429, 500, 502, 503, 504]  # retry on these status codes
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.logger.info("Initialized ImmobiliareScraper with base URL: %s", self.base_url)
    
    def _get_random_headers(self) -> Dict[str, str]:
        """Generate random headers for each request.
        
        Returns:
            Dict[str, str]: Headers dictionary
        """
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "DNT": "1"
        }
        return headers
    
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
            # Add random jitter to delay
            base_delay = random.uniform(self.min_delay, self.max_delay)
            jitter = random.uniform(-2, 2)  # Add ±2 seconds of jitter
            delay = max(0, base_delay + jitter)
            
            self.logger.debug("Waiting %.2f seconds before request", delay)
            time.sleep(delay)
            
            # Make request with random headers
            headers = self._get_random_headers()
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                raise ScrapingError(f"Request failed with status code {response.status_code}")
                
            return response
            
        except requests.RequestException as e:
            raise ScrapingError(f"Failed to make request: {e}")
    
    def validate_url(self, url: str) -> None:
        """Validate that the URL is appropriate for immobiliare.it.
        
        Args:
            url: URL to validate
            
        Raises:
            ValidationError: If the URL is invalid
        """
        self.logger.debug("Validating URL: %s", url)
        if not self.base_url in url:
            self.logger.error("Invalid URL: missing base URL %s", self.base_url)
            raise ValidationError(f"Given URL must include '{self.base_url}'")
        
        if "mapCenter" in url:
            self.logger.error("Invalid URL: contains 'mapCenter' which uses a different API")
            raise ValidationError("Given URL must not include 'mapCenter' as it uses another API to retrieve data")
        
        if "search-list" in url:
            self.logger.error("Invalid URL: contains 'search-list' which uses a different API")
            raise ValidationError("Given URL must not include 'search-list' as it uses another API to retrieve data")
        self.logger.debug("URL validation successful")
    
    def extract_data(self, response: requests.Response) -> List[RealEstate]:
        """Extract JSON data from the response and convert to RealEstate objects.
        
        Args:
            response: HTTP response to extract data from
            
        Returns:
            List of RealEstate objects
            
        Raises:
            ScrapingError: If there's an error extracting data
        """
        self.logger.debug("Extracting data from response (status code: %d)", response.status_code)
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
            
            if not script_tag:
                self.logger.error("Failed to find __NEXT_DATA__ script tag in response")
                raise ScrapingError("Could not find __NEXT_DATA__ script tag")
                
            json_data = script_tag.text
            data = json.loads(json_data)
            results = data["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["results"]
            
            # Process surface data and convert to RealEstate objects
            real_estates = []
            for record in results:
                if "realEstate" in record and "properties" in record["realEstate"]:
                    # Process surface data
                    surface = record["realEstate"]["properties"][0].get("surface")
                    if surface:
                        surface_match = re.search(r'(\d+\.?\d*)', surface)
                        if surface_match:
                            record["realEstate"]["properties"][0]["surface_value"] = float(surface_match.group(1))
                    
                    # Convert to RealEstate object
                    try:
                        real_estate = RealEstate.from_dict(record)
                        real_estates.append(real_estate)
                    except Exception as e:
                        self.logger.warning("Failed to convert record to RealEstate object: %s", str(e))
                        continue
            
            self.logger.info("Successfully extracted %d real estate listings", len(real_estates))
            return real_estates
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to extract JSON data: %s", str(e), exc_info=True)
            raise ScrapingError(f"Failed to extract JSON data: {e}")
    
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
        self.logger.debug("Generating URL for page %d", page_number)
        try:
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)
            query_params['pag'] = [str(page_number)]
            
            next_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                urlencode(query_params, doseq=True),
                parsed_url.fragment
            ))
            self.logger.debug("Generated next page URL: %s", next_url)
            return next_url
        except Exception as e:
            self.logger.error("Failed to generate next page URL: %s", str(e), exc_info=True)
            raise ValidationError(f"Failed to generate next page URL: {e}")
    
    def scrape_page(self, url: str) -> List[RealEstate]:
        """Scrape a single page of real estate listings.
        
        Args:
            url: URL of the page to scrape
            
        Returns:
            List of RealEstate objects
            
        Raises:
            ScrapingError: If there's an error during scraping
        """
        self.logger.info("Scraping page: %s", url)
        try:
            response = self.get_page(url)
            return self.extract_data(response)
        except Exception as e:
            self.logger.error("Failed to scrape page %s: %s", url, str(e), exc_info=True)
            raise ScrapingError(f"Failed to scrape page: {e}")
    
    def scrape_all_pages(self, start_url: str, max_pages: Optional[int] = None) -> List[RealEstate]:
        """Scrape all pages of listings.
        
        Args:
            start_url: URL to start scraping from
            max_pages: Optional maximum number of pages to scrape
            
        Returns:
            List of all RealEstate objects
            
        Raises:
            ScrapingError: If there's an error during scraping
        """
        self.logger.info("Starting to scrape all pages from: %s (max pages: %s)", 
                        start_url, 
                        str(max_pages) if max_pages else "unlimited")
        
        all_listings = []
        current_url = start_url
        page_count = 0
        
        while current_url and (max_pages is None or page_count < max_pages):
            try:
                page_count += 1
                self.logger.info("Scraping page %d: %s", page_count, current_url)
                
                page_listings = self.scrape_page(current_url)
                
                if not page_listings:
                    self.logger.warning("No listings found on page %d", page_count)
                    break
                
                all_listings.extend(page_listings)
                self.logger.info("Total listings collected so far: %d", len(all_listings))
                
                # Get the next page URL
                page_count += 1
                current_url = self.get_next_page_url(current_url, page_count)
                
                if current_url:
                    self.logger.debug("Waiting before next page request...")
                    time.sleep(random.uniform(self.min_delay, self.max_delay))
                
            except Exception as e:
                self.logger.error("Error scraping page %d: %s", page_count, str(e), exc_info=True)
                raise ScrapingError(f"Failed to scrape page {page_count}: {e}")
        
        self.logger.info("Finished scraping. Total pages scraped: %d, Total listings: %d", 
                        page_count, 
                        len(all_listings))
        return all_listings 