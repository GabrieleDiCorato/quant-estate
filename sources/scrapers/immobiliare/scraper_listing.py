import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
import re
import random

from sources.config.model.storage_settings import CsvStorageSettings
from sources.datamodel.enumerations import Source
from sources.datamodel.listing_id import ListingId
from sources.logging import logging_utils
from sources.scrapers.selenium_scraper import SeleniumScraper
from sources.storage.abstract_storage import Storage
from sources.storage.file_storage import FileStorage

logger = logging.getLogger(__name__)
BASE_URL = "https://www.immobiliare.it/"
URL_PREFIX = "https://www.immobiliare.it/annunci/"

class ImmobiliareListingScraper(SeleniumScraper):
    """Scraper for Immobiliare.it using Selenium. Given the URL for a specific listing, it extracts all relevant details."""

    def __init__(
        self,
        storage: Storage,
        scrape_url: str,
        listing_id: ListingId,
        base_url: str = BASE_URL,
        **kwargs,
    ):
        """Initialize the Immobiliare scraper with specific settings."""
        super().__init__(storage, base_url, scrape_url=scrape_url, **kwargs)
        if not scrape_url.startswith(URL_PREFIX):
            raise ValueError(f"scrape_url must start with [{URL_PREFIX}], got [{scrape_url}]")
        self.listing_id = listing_id

    def scrape(self):
        """Main scraping method to collect property IDs."""

        # Automatically closes driver after use
        with self.get_driver() as driver:
            # self.warmup_driver(driver)

            # Navigate to the page
            logger.info("Navigating to scrape URL: %s", self.scrape_url)
            self.get_page(driver, self.scrape_url, wait_for_element=("CSS_SELECTOR", "h1.styles_ld-title__title__Ww2Gb"))

            # Close cookies banner if present (already present in warmup_driver)
            self._close_cookies(driver)
            self._realistic_wait()

            # Close login popup if present
            self._close_login_popup(driver)
            self._realistic_wait()

            # Random scroll before scraping
            driver.execute_script(f"window.scrollTo(0, {random.randint(100, 700)});")

            # Extract main components
            title: str = self._get_title(driver)
            price: str = self._get_price(driver)
            location_parts: list[str] = self._get_location(driver)

            # Extract description title and extended description
            description_title, extended_description = self._get_description(driver)

            # Open characteristics dialog
            dialog_element = self._open_characteristics_dialog(driver)
            if dialog_element is None:
                logger.warning("Failed to open characteristics dialog, skipping characteristics extraction.")
            else:
                logger.info("Successfully opened characteristics dialog, ready for data extraction")

                # In your scrape() method, after opening the dialog:
                characteristics = self._extract_characteristics(dialog_element)
                logger.info("Extracted characteristics: %s", characteristics)

    def _get_element(self, driver, by: str, value: str):
        """Helper method to get an element by its locator."""
        try:
            return driver.find_element(by, value)
        except Exception as e:
            logger.error("Element not found: %s, %s", by, value)
            raise ValueError(f"Element not found: {by}, {value}") from e

    def _get_title(self, driver) -> str:
        title_elem = self._get_element(driver, By.CSS_SELECTOR, "h1.styles_ld-title__title__Ww2Gb")
        title = title_elem.text.strip()
        logger.debug("Extracted title: %s", title)
        return title

    def _get_price(self, driver) -> str:
        price_elem = self._get_element(driver, By.CSS_SELECTOR, "div.Price_price__mzj0D span")
        price = price_elem.text.strip()
        logger.debug("Extracted price: %s", price)
        return price

    def _get_location(self, driver) -> list[str]:
        location_spans = driver.find_elements(By.CSS_SELECTOR, "button.styles_ld-blockTitle__link__paCwh span.styles_ld-blockTitle__location__n2mZJ")
        if not location_spans:
            logger.error("Location elements not found")
            raise ValueError("Location elements not found on the page")
        location_parts = [span.text.strip() for span in location_spans]
        logger.debug("Extracted location: %s", location_parts)
        return location_parts

    def _get_description(self, driver) -> tuple[str, str]:
        """Extract description title and extended description.
        
        Returns:
            tuple[str, str]: (title, extended_description) both normalized to single lines
        """
        try:
            # Scroll to the description section
            description_section = driver.find_element(By.CSS_SELECTOR, "div[data-tracking-key='description']")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", description_section)
            self._realistic_wait()

            # Extract the description title
            title_elem = driver.find_element(By.CSS_SELECTOR, "p.styles_ld-descriptionHeading__title__ifRR2")
            title = self._normalize_text(title_elem.text)

            # Click the "leggi tutto" button to expand full description
            read_more_button = driver.find_element(By.CSS_SELECTOR, "button.styles_in-readAll__action___B8HW")
            driver.execute_script("arguments[0].click();", read_more_button)
            self._realistic_wait()

            # Extract the extended description after expansion
            description_container = driver.find_element(By.CSS_SELECTOR, "div.styles_in-readAll__04LDT div")
            extended_description = self._normalize_text(description_container.text)

            logger.debug("Extracted description title: %s", title)
            logger.debug("Extracted extended description length: %d chars", len(extended_description))

            return title, extended_description

        except Exception as e:
            logger.warning("Error extracting description: %s", str(e))
            return ("", "")

    def _normalize_text(self, text: str) -> str:
        """Normalize text to a single line by handling whitespace and special characters.
        
        Args:
            text: Raw text to normalize
            
        Returns:
            str: Normalized single-line text
        """
        if not text:
            return ""

        # Strip leading/trailing whitespace
        normalized = text.strip()
        # Replace multiple consecutive whitespace characters (including newlines, tabs, spaces) with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        # Remove any remaining control characters except basic ones
        normalized = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', normalized)
        return normalized

    def _open_characteristics_dialog(self, driver) -> WebElement | None:
        """Navigate to and click the 'Vedi tutte le caratteristiche' button, then wait for dialog.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            WebElement: The dialog container element if found, None if failed
        """
        try:
            logger.info("Looking for 'Vedi tutte le caratteristiche' button")
            # Find the characteristics button
            characteristics_button = driver.find_element(By.CSS_SELECTOR, "button.styles_ld-primaryFeatures__openDialogButton___8v4x")

            # Scroll to the button to ensure it's visible
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", characteristics_button)
            self._realistic_wait()
            logger.info("Found 'Vedi tutte le caratteristiche' button, clicking it")

            # Wait for the button to be clickable
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.styles_ld-primaryFeatures__openDialogButton___8v4x"))
            )

            # Click the button using JavaScript for reliability
            driver.execute_script("arguments[0].click();", characteristics_button)
            logger.info("Successfully clicked 'Vedi tutte le caratteristiche' button")

            # Wait for the dialog to appear and return it
            logger.info("Waiting for characteristics dialog to appear...")
            dialog_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.nd-dialogFrame__container"))
            )
            logger.info("Successfully found characteristics dialog")

            # Small wait to ensure dialog is fully loaded
            self._realistic_wait()

            return dialog_element

        except Exception as e:
            logger.warning("Error opening characteristics dialog: %s", str(e))
            return None

    def _extract_characteristics(self, dialog_element: WebElement) -> dict[str, str]:
        """Extract all key-value pairs from the characteristics dialog.
        
        Args:
            dialog_element: The dialog container WebElement
            
        Returns:
            dict[str, str]: Dictionary with characteristic names as keys and values as values
        """
        characteristics = {}

        try:
            # Find all feature containers within the dialog
            feature_elements = dialog_element.find_elements(By.CSS_SELECTOR, "div.styles_ld-primaryFeaturesDialogSection__feature__Maf3F")
            logger.debug("Found %d characteristic features in dialog", len(feature_elements))

            for feature in feature_elements:
                try:
                    # Extract the key (dt element)
                    key_element = feature.find_element(By.CSS_SELECTOR, "dt.styles_ld-primaryFeaturesDialogSection__featureTitle__VI7c0")
                    key = self._normalize_text(key_element.text)

                    # Extract the value (dd element)
                    value_element = feature.find_element(By.CSS_SELECTOR, "dd.styles_ld-primaryFeaturesDialogSection__featureDescription__G9ZGQ")
                    value = self._normalize_text(value_element.text)

                    if key and value:  # Only add non-empty pairs
                        characteristics[key] = value

                except Exception as feature_error:
                    logger.warning("Error extracting feature: %s", str(feature_error))
                    continue

            logger.info("Successfully extracted %d characteristics", len(characteristics))
            return characteristics

        except Exception as e:
            logger.error("Error extracting characteristics from dialog: %s", str(e))
            return characteristics

    def to_next_page(self, driver, current_page: int) -> bool:
        raise NotImplementedError("Pagination is not defined while scraping a specific listing")


# uv run --env-file sources/resources/config.dev.env sources/scrapers/immobiliare/scraper_listing.py
# See im_pipeline_listing.ipynb for a more interactive usage and extensive configuration using env variables and config files.
if __name__ == "__main__":  
    logging_utils.setup_logging(config_path="sources/resources/logging.yaml")

    storage: Storage = FileStorage(ListingId, CsvStorageSettings())
    test_listing_id = ListingId(
        source=Source.IMMOBILIARE, 
        source_id="122361988",
        title="Test Listing",
        url="https://www.immobiliare.it/annunci/122361988/"
    )
    scraper = ImmobiliareListingScraper(
        storage,
        scrape_url="https://www.immobiliare.it/annunci/122361988/",
        listing_id=test_listing_id
    )
    scraper.scrape()
