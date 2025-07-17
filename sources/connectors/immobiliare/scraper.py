"""
Scraper implementation for immobiliare.it.
"""

import logging
import re
import time
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import random

from ..abstract_scraper import Scraper
from ...exceptions import (
    ScrapingError, ValidationError, ConfigurationError,
    InvalidURLError, DataExtractionError, RequestError
)
from ...datamodel.listing_details import ListingDetails

logger = logging.getLogger(__name__)

class ImmobiliareScraper(Scraper):
    """Scraper implementation for immobiliare.it."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the scraper with configuration.
        
        Args:
            config: Configuration dictionary containing scraper settings
            
        Raises:
            ConfigurationError: If required configuration keys are missing
        """
        super().__init__(config)
        logger.info("Initialized ImmobiliareScraper with base URL: %s", self.base_url)

    def validate_url(self, url: str) -> None:
        """Validate that the URL is appropriate for immobiliare.it.
        
        Args:
            url: URL to validate
            
        Raises:
            ValidationError: If the URL is invalid
        """
        logger.debug("Validating URL: %s", url)
        if not self.base_url in url:
            logger.error("Invalid URL: missing base URL %s", self.base_url)
            raise ValidationError(f"Given URL must include '{self.base_url}'")

        if "mapCenter" in url:
            logger.error("Invalid URL: contains 'mapCenter' which uses a different API")
            raise ValidationError("Given URL must not include 'mapCenter' as it uses another API to retrieve data")

        if "search-list" in url:
            logger.error("Invalid URL: contains 'search-list' which uses a different API")
            raise ValidationError("Given URL must not include 'search-list' as it uses another API to retrieve data")
        logger.debug("URL validation successful")

    def get_full_description(self, property_id: str) -> str:
        """Fetch the full description from the property detail page.
        
        Args:
            property_id: The ID of the property
            
        Returns:
            str: The full description of the property
            
        Raises:
            ScrapingError: If there's an error fetching the description
        """
        try:
            # Construct the detail page URL
            detail_url = f"{self.base_url}/annunci/{property_id}"
            logger.debug("Fetching full description from: %s", detail_url)

            # Add a small delay before the request
            time.sleep(random.uniform(1, 2))

            # Get the detail page
            response = self.get_page(detail_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the description element
            description_elem = soup.find("div", {"class": "description"})
            if description_elem:
                full_description = description_elem.get_text(strip=True)
                logger.debug("Found full description for property %s: %s", 
                                property_id, full_description[:100] + "..." if len(full_description) > 100 else full_description)
                return full_description

            logger.warning("Could not find description element for property %s", property_id)
            return ""

        except Exception as e:
            logger.error("Error fetching full description for property %s: %s", 
                            property_id, str(e), exc_info=True)
            return ""

    def extract_data(self, response: requests.Response) -> List[ListingDetails]:
        """Extract JSON data from the response and convert to RealEstate objects.
        
        Args:
            response: HTTP response to extract data from
            
        Returns:
            List of RealEstate objects
            
        Raises:
            ScrapingError: If there's an error extracting data
        """
        logger.debug("Extracting data from response (status code: %d)", response.status_code)
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

            if not script_tag:
                logger.error("Failed to find __NEXT_DATA__ script tag in response")
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

                    # Process description data
                    properties = record["realEstate"]["properties"][0]
                    raw_description = properties.get("description")
                    logger.debug(f"Raw description for property {record["realEstate"]["id"]}: {raw_description}")

                    # Convert to RealEstate object
                    try:
                        real_estate = self.placeholder(record)
                        real_estates.append(real_estate)
                    except Exception as e:
                        logger.warning("Failed to convert record to RealEstate object: %s", str(e))
                        continue

            logger.info("Successfully extracted %d real estate listings", len(real_estates))
            return real_estates

        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            logger.error("Failed to extract JSON data: %s", str(e), exc_info=True)
            raise ScrapingError(f"Failed to extract JSON data: {e}")

    def placeholder(self, data) -> ListingDetails:
        properties = data["realEstate"]["properties"][0]
        location = properties["location"]

        return ListingDetails(
            id=str(data["realEstate"]["id"]),
            url=data["seo"]["url"],
            contract=data["realEstate"]["contract"],
            agency_id=data["realEstate"]["advertiser"].get("agency", {}).get("label"),
            agency_url=data["realEstate"]["advertiser"].get("agency", {}).get("agencyUrl"),
            agency_name=data["realEstate"]["advertiser"].get("agency", {}).get("displayName"),
            is_private_ad=data["realEstate"]["advertiser"].get("agency") is None,
            is_new=bool(data["realEstate"]["isNew"]),
            is_luxury=bool(data["realEstate"]["luxury"]),
            formatted_price=data["realEstate"]["price"]["formattedValue"],
            price=data["realEstate"]["price"].get("value"),
            bathrooms=properties.get("bathrooms"),
            bedrooms=properties.get("bedRoomsNumber"),
            floor=properties.get("floor", {}).get("abbreviation"),
            formatted_floor=properties.get("floor", {}).get("value"),
            total_floors=properties.get("floors"),
            condition=properties.get("condition"),
            rooms=properties.get("rooms"),
            has_elevators=bool(properties.get("hasElevators")),
            surface=properties.get("surface_value"),  # Use the processed surface value
            surface_formatted=properties.get("surface"),
            type=properties["typologyGA4Translation"],
            caption=properties.get("caption"),
            category=properties["category"]["name"],
            description=properties.get("description"),
            heating_type=properties.get("energy", {}).get("heatingType"),
            air_conditioning=properties.get("energy", {}).get("airConditioning"),
            latitude=float(location["latitude"]),
            longitude=float(location["longitude"]),
            region=location["region"],
            province=location["province"],
            macrozone=location["macrozone"],
            microzone=location["microzone"],
            city=location["city"],
            country=location["nation"]["id"]
        )

    def get_page_url(self, current_url: str, page_number: int) -> str:
        """Generate the URL for the next page of results.
        
        Args:
            current_url: Current page URL
            page_number: Next page number
            
        Returns:
            str: URL for the next page
            
        Raises:
            ValidationError: If the generated URL is invalid
        """
        logger.debug("Generating URL for page %d", page_number)
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
            logger.debug("Generated next page URL: %s", next_url)
            return next_url
        except Exception as e:
            logger.error("Failed to generate next page URL: %s", str(e), exc_info=True)
            raise ValidationError(f"Failed to generate next page URL: {e}")

    def scrape_page(self, url: str) -> List[ListingDetails]:
        """Scrape a single page of real estate listings.
        
        Args:
            url: URL of the page to scrape
            
        Returns:
            List of RealEstate objects
            
        Raises:
            ScrapingError: If there's an error during scraping
        """
        logger.info("Scraping page: %s", url)
        try:
            response = self.get_page(url)
            return self.extract_data(response)
        except Exception as e:
            logger.error("Failed to scrape page %s: %s", url, str(e), exc_info=True)
            raise ScrapingError(f"Failed to scrape page: {e}")

    def scrape_all_pages(self, start_url: str, max_pages: Optional[int] = None) -> List[ListingDetails]:
        """Scrape all pages of listings.
        
        Args:
            start_url: URL to start scraping from
            max_pages: Optional maximum number of pages to scrape
            
        Returns:
            List of all RealEstate objects
            
        Raises:
            ScrapingError: If there's an error during scraping
        """
        logger.info("Starting to scrape all pages from: %s (max pages: %s)", 
                        start_url, 
                        str(max_pages) if max_pages else "unlimited")

        all_listings = []
        current_url = start_url
        page_count = 0

        while current_url and (max_pages is None or page_count < max_pages):
            try:
                page_count += 1
                logger.info("Scraping page %d: %s", page_count, current_url)

                page_listings = self.scrape_page(current_url)

                if not page_listings:
                    logger.warning("No listings found on page %d", page_count)
                    break

                all_listings.extend(page_listings)
                logger.info("Total listings collected so far: %d", len(all_listings))

                # Get the next page URL
                page_count += 1
                current_url = self.get_page_url(current_url, page_count)

                if current_url:
                    logger.debug("Waiting before next page request...")
                    time.sleep(random.uniform(self.min_delay, self.max_delay))

            except Exception as e:
                logger.error("Error scraping page %d: %s", page_count, str(e), exc_info=True)
                raise ScrapingError(f"Failed to scrape page {page_count}: {e}")

        logger.info("Finished scraping. Total pages scraped: %d, Total listings: %d", 
                        page_count, 
                        len(all_listings))
        return all_listings 
