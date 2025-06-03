"""
Scraper implementation for immobiliare.it.
"""

import re
import time
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse

from ..base import BaseScraper
from .models import RealEstate
from .exceptions import InvalidURLError, DataExtractionError, ScrapingError
from ...utils.logging import get_logger

# Set up logging
logger = get_logger("quant_estate.scraper.immobiliare")

class ImmobiliareScraper(BaseScraper):
    """Scraper implementation for immobiliare.it."""
    
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize the scraper."""
        super().__init__(base_url)
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.logger = get_logger("quant_estate.scraper.immobiliare")
        self.logger.info("Initialized ImmobiliareScraper with base URL: %s", base_url)
    
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

    def scrape_page(self, url: str) -> List[Dict[str, Any]]:
        """Scrape a single page of real estate listings."""
        self.logger.info("Scraping page: %s", url)
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            listings = soup.find_all('div', class_='listing-item')
            
            if not listings:
                self.logger.warning("No listings found on page: %s", url)
                return []
            
            self.logger.info("Found %d listings on page", len(listings))
            results = []
            
            for listing in listings:
                try:
                    data = self._extract_listing_data(listing)
                    if data:
                        results.append(data)
                except Exception as e:
                    self.logger.error("Failed to extract listing data: %s", str(e), exc_info=True)
                    continue
            
            self.logger.info("Successfully extracted %d listings from page", len(results))
            return results
            
        except requests.RequestException as e:
            self.logger.error("Failed to fetch page %s: %s", url, str(e), exc_info=True)
            raise ScrapingError(f"Failed to fetch page: {e}")
        except Exception as e:
            self.logger.error("Unexpected error while scraping page %s: %s", url, str(e), exc_info=True)
            raise ScrapingError(f"Unexpected error: {e}")
    
    def _extract_listing_data(self, listing: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract data from a single listing element."""
        try:
            # Extract basic information
            title = listing.find('h2', class_='listing-title').text.strip()
            price = listing.find('div', class_='listing-price').text.strip()
            location = listing.find('div', class_='listing-location').text.strip()
            
            # Extract details
            details = {}
            detail_elements = listing.find_all('div', class_='listing-detail')
            for element in detail_elements:
                key = element.find('span', class_='detail-label').text.strip()
                value = element.find('span', class_='detail-value').text.strip()
                details[key] = value
            
            # Extract URL
            url_element = listing.find('a', class_='listing-link')
            url = urljoin(self.base_url, url_element['href']) if url_element else None
            
            self.logger.debug("Extracted listing: %s in %s", title, location)
            
            return {
                'title': title,
                'price': price,
                'location': location,
                'details': details,
                'url': url
            }
            
        except Exception as e:
            self.logger.error("Failed to extract listing data: %s", str(e), exc_info=True)
            return None
    
    def get_next_page_url(self, current_url: str, soup: BeautifulSoup) -> Optional[str]:
        """Get the URL of the next page if available."""
        try:
            next_button = soup.find('a', class_='next-page')
            if next_button and 'href' in next_button.attrs:
                next_url = urljoin(self.base_url, next_button['href'])
                self.logger.debug("Found next page URL: %s", next_url)
                return next_url
            self.logger.debug("No next page found for URL: %s", current_url)
            return None
        except Exception as e:
            self.logger.error("Error finding next page URL: %s", str(e), exc_info=True)
            return None
    
    def scrape_all_pages(self, start_url: str, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scrape all pages of listings."""
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
                
                response = requests.get(current_url, headers=self.headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                page_listings = self.scrape_page(current_url)
                
                if not page_listings:
                    self.logger.warning("No listings found on page %d", page_count)
                    break
                
                all_listings.extend(page_listings)
                self.logger.info("Total listings collected so far: %d", len(all_listings))
                
                current_url = self.get_next_page_url(current_url, soup)
                
                if current_url:
                    self.logger.debug("Waiting before next page request...")
                    time.sleep(2)  # Be nice to the server
                
            except Exception as e:
                self.logger.error("Error scraping page %d: %s", page_count, str(e), exc_info=True)
                break
        
        self.logger.info("Finished scraping. Total pages scraped: %d, Total listings: %d", 
                        page_count, 
                        len(all_listings))
        return all_listings 