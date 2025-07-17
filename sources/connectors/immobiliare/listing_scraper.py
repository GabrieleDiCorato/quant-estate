"""
Selenium-based scraper implementation for immobiliare.it listings.
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..selenium_scraper import SeleniumScraper
from ...exceptions import (
    ScrapingError, ValidationError, ConfigurationError,
    InvalidURLError, DataExtractionError
)
from ...datamodel.listing_details import ListingDetails
from ...datamodel.listing_id import ListingId
from ...datamodel.enumerations import Source, ContractType, PropertyType

logger = logging.getLogger(__name__)

class ImmobiliareSeleniumScraper(SeleniumScraper):
    """Selenium-based scraper implementation for immobiliare.it."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the scraper with configuration.
        
        Args:
            config: Configuration dictionary containing scraper settings
            
        Raises:
            ConfigurationError: If required configuration keys are missing
        """
        super().__init__(config)
        logger.info("Initialized ImmobiliareSeleniumScraper with base URL: %s", self.base_url)

    def validate_url(self, url: str) -> None:
        """Validate that the URL is appropriate for immobiliare.it.
        
        Args:
            url: URL to validate
            
        Raises:
            ValidationError: If the URL is invalid
        """
        logger.debug("Validating URL: %s", url)
        if self.base_url not in url:
            logger.error("Invalid URL: missing base URL %s", self.base_url)
            raise ValidationError(f"Given URL must include '{self.base_url}'")

        if "mapCenter" in url:
            logger.error("Invalid URL: contains 'mapCenter' which uses a different API")
            raise ValidationError("Given URL must not include 'mapCenter' as it uses another API to retrieve data")

        if "search-list" in url:
            logger.error("Invalid URL: contains 'search-list' which uses a different API")
            raise ValidationError("Given URL must not include 'search-list' as it uses another API to retrieve data")
        
        logger.debug("URL validation successful")

    def scrape_listings(self, url: str) -> List[ListingDetails]:
        """Scrape listings from the given URL using Selenium.
        
        Args:
            url: URL to scrape listings from
            
        Returns:
            List of ListingDetails objects
            
        Raises:
            ScrapingError: If there's an error scraping the listings
        """
        self.validate_url(url)
        
        logger.info("Starting to scrape listings from: %s", url)
        
        with self.get_driver() as driver:
            try:
                # Navigate to the page and wait for listings to load
                self.get_page(driver, url, wait_for_element=("class_name", "listing-item"))
                
                # Handle cookie consent and other popups
                self._handle_popups(driver)
                
                # Scroll to load more listings if needed
                self._scroll_to_load_listings(driver)
                
                # Extract __NEXT_DATA__ JSON with property data
                next_data = self._extract_next_data(driver)
                
                if not next_data:
                    logger.warning("No __NEXT_DATA__ found on page")
                    return []
                
                # Parse listings from JSON data
                listings = self._parse_listings_from_json(next_data)
                
                logger.info("Successfully scraped %d listings", len(listings))
                return listings
                
            except Exception as e:
                logger.error("Error scraping listings: %s", str(e), exc_info=True)
                raise ScrapingError(f"Failed to scrape listings: {e}")

    def _handle_popups(self, driver) -> None:
        """Handle cookie consent and other popups that might appear.
        
        Args:
            driver: WebDriver instance
        """
        try:
            # Wait for and dismiss cookie consent
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
            )
            cookie_button.click()
            logger.debug("Dismissed cookie consent popup")
            time.sleep(1)
        except TimeoutException:
            logger.debug("No cookie consent popup found")
        
        try:
            # Handle other potential popups
            close_buttons = driver.find_elements(By.CSS_SELECTOR, "[data-testid='close-button'], .close-button, .popup-close")
            for button in close_buttons:
                if button.is_displayed():
                    button.click()
                    logger.debug("Dismissed popup")
                    time.sleep(0.5)
        except Exception as e:
            logger.debug("No additional popups to handle: %s", str(e))

    def _scroll_to_load_listings(self, driver) -> None:
        """Scroll the page to load more listings if infinite scroll is enabled.
        
        Args:
            driver: WebDriver instance
        """
        try:
            # Check if there's a "Load more" button or infinite scroll
            initial_listings = len(driver.find_elements(By.CSS_SELECTOR, ".listing-item"))
            logger.debug("Initial listings count: %d", initial_listings)
            
            # Scroll to bottom to trigger loading
            self.scroll_to_bottom(driver, pause_time=2.0)
            
            # Wait for potential new listings to load
            time.sleep(3)
            
            final_listings = len(driver.find_elements(By.CSS_SELECTOR, ".listing-item"))
            logger.debug("Final listings count after scroll: %d", final_listings)
            
        except Exception as e:
            logger.debug("Error during scroll loading: %s", str(e))

    def _extract_next_data(self, driver) -> Optional[Dict[str, Any]]:
        """Extract __NEXT_DATA__ JSON from the page.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            Dictionary containing the parsed JSON data, or None if not found
        """
        try:
            # Find the __NEXT_DATA__ script tag
            script_element = driver.find_element(By.ID, "__NEXT_DATA__")
            script_content = script_element.get_attribute("innerHTML")
            
            if not script_content:
                logger.warning("__NEXT_DATA__ script tag found but empty")
                return None
            
            # Parse JSON data
            json_data = json.loads(script_content)
            logger.debug("Successfully extracted __NEXT_DATA__ JSON")
            return json_data
            
        except NoSuchElementException:
            logger.warning("__NEXT_DATA__ script tag not found")
            return None
        except json.JSONDecodeError as e:
            logger.error("Failed to parse __NEXT_DATA__ JSON: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error extracting __NEXT_DATA__: %s", str(e))
            return None

    def _parse_listings_from_json(self, json_data: Dict[str, Any]) -> List[ListingDetails]:
        """Parse listings from the extracted JSON data.
        
        Args:
            json_data: Parsed JSON data from __NEXT_DATA__
            
        Returns:
            List of ListingDetails objects
        """
        try:
            listings = []
            
            # Navigate through the JSON structure to find listings
            # The structure may vary, so we need to explore it
            page_props = json_data.get("props", {}).get("pageProps", {})
            
            # Look for listings in various possible locations
            listing_data = None
            if "listings" in page_props:
                listing_data = page_props["listings"]
            elif "results" in page_props:
                listing_data = page_props["results"]
            elif "properties" in page_props:
                listing_data = page_props["properties"]
            
            if not listing_data:
                logger.warning("No listing data found in JSON structure")
                return []
            
            # Handle different data structures
            if isinstance(listing_data, dict):
                # If it's a dict, look for items or results
                items = listing_data.get("items", listing_data.get("results", []))
            elif isinstance(listing_data, list):
                items = listing_data
            else:
                logger.warning("Unexpected listing data structure")
                return []
            
            # Parse each listing
            for item in items:
                try:
                    listing = self._parse_single_listing(item)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    logger.warning("Error parsing single listing: %s", str(e))
                    continue
            
            logger.info("Successfully parsed %d listings from JSON", len(listings))
            return listings
            
        except Exception as e:
            logger.error("Error parsing listings from JSON: %s", str(e), exc_info=True)
            return []

    def _parse_single_listing(self, item: Dict[str, Any]) -> Optional[ListingDetails]:
        """Parse a single listing item from JSON data.
        
        Args:
            item: Single listing item from JSON
            
        Returns:
            ListingDetails object or None if parsing fails
        """
        try:
            # Extract basic information
            listing_id = ListingId(
                source=Source.IMMOBILIARE,
                source_id=str(item.get("id", "")),
                title=item.get("title", item.get("name", "Property Listing")),
                url=item.get("url", "")
            )
            
            # Price information
            price_info = item.get("price", {})
            formatted_price = price_info.get("formatted", "")
            price_eur = float(price_info.get("value", 0))
            
            # Property details
            property_info = item.get("property", {})
            
            # Create ListingDetails object
            listing = ListingDetails(
                listing_id=listing_id,
                formatted_price=formatted_price,
                price_eur=price_eur,
                formatted_maintenance_fee=None,  # Extract if available
                maintenance_fee=None,
                type=self._parse_property_type(property_info.get("type", "")),
                contract=self._parse_contract_type(item.get("contract", "")),
                condition=None,  # Extract if available
                is_new=None,
                is_luxury=None,
                surface_formatted=property_info.get("surface", {}).get("formatted", ""),
                surface=property_info.get("surface", {}).get("value"),
                rooms=property_info.get("rooms"),
                floor=property_info.get("floor"),
                total_floors=property_info.get("totalFloors"),
                bathrooms=property_info.get("bathrooms"),
                bedrooms=property_info.get("bedrooms"),
                balcony=property_info.get("balcony"),
                terrace=property_info.get("terrace"),
                elevator=property_info.get("elevator"),
                garden=property_info.get("garden"),
                cellar=property_info.get("cellar"),
                basement=property_info.get("basement"),
                furnished=property_info.get("furnished"),
                build_year=property_info.get("buildYear"),
                considerge=property_info.get("concierge"),
                is_accessible=property_info.get("accessible"),
                description=item.get("description", ""),
                other_amenities=item.get("amenities", []),
                heating_type=None,  # Extract if available
                air_conditioning=None,  # Extract if available
                energy_class=None,  # Extract if available
                city=item.get("location", {}).get("city", ""),
                country=item.get("location", {}).get("country", "IT"),
                address=item.get("location", {}).get("address", ""),
                parking_info=property_info.get("parking", "")
            )
            
            return listing
            
        except Exception as e:
            logger.error("Error parsing single listing: %s", str(e), exc_info=True)
            return None

    def _parse_property_type(self, type_str: str) -> PropertyType:
        """Parse property type from string.
        
        Args:
            type_str: Property type string
            
        Returns:
            PropertyType enum value
        """
        type_lower = type_str.lower()
        if "appartamento" in type_lower or "apartment" in type_lower:
            return PropertyType.APARTMENT
        elif "casa" in type_lower or "house" in type_lower:
            return PropertyType.HOUSE
        elif "commerciale" in type_lower or "commercial" in type_lower:
            return PropertyType.COMMERCIAL
        elif "terreno" in type_lower or "land" in type_lower:
            return PropertyType.LAND
        elif "industriale" in type_lower or "industrial" in type_lower:
            return PropertyType.INDUSTRIAL
        else:
            return PropertyType.APARTMENT  # Default

    def _parse_contract_type(self, contract_str: str) -> ContractType:
        """Parse contract type from string.
        
        Args:
            contract_str: Contract type string
            
        Returns:
            ContractType enum value
        """
        contract_lower = contract_str.lower()
        if "vendita" in contract_lower or "sale" in contract_lower:
            return ContractType.SALE
        elif "affitto" in contract_lower or "rent" in contract_lower:
            return ContractType.RENT
        else:
            return ContractType.SALE  # Default