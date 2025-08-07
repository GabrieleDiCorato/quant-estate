import logging
import re
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement

from sources.config.model.scraper_settings import ScraperImmobiliareIdSettings
from sources.config.model.storage_settings import CsvStorageSettings
from sources.datamodel.listing_id import ListingId
from sources.logging import logging_utils
from sources.scrapers.selenium_scraper import SeleniumScraper
from sources.storage.abstract_storage import Storage
from sources.storage.file_storage import FileStorage

SOURCE = "immobiliare"

class ImmobiliareIdScraper(SeleniumScraper):
    """Scraper for Immobiliare.it using Selenium."""

    def __init__(
        self,
        storage: Storage,
        settings: ScraperImmobiliareIdSettings,
        scrape_url: str = "https://www.immobiliare.it/vendita-case/milano/"
    ):
        """Initialize the Immobiliare scraper with specific settings."""
        super().__init__(storage, settings)

        if not isinstance(settings, ScraperImmobiliareIdSettings):
            raise TypeError(f"Expected ScraperImmobiliareIdSettings, got {type(settings).__name__}")
        self.settings = settings

        self.scrape_url = scrape_url

        # Create instance-specific logger
        self.logger = logging.getLogger(f"{__name__}.{self._instance_id}")

    @classmethod
    def _get_url_with_params(cls, settings: ScraperImmobiliareIdSettings, scrape_url) -> str:
        """Construct the scrape URL with sorting and filtering parameters."""
        url = scrape_url
        if url[-1] != "/":
            url += "/"
        if settings.use_sorting:
            url += f"?{settings.sorting_url_param}"
        if settings.use_filtering:
            if "?" in url:
                url += "&"
            else:
                url += "?"
            url += settings.filter_url_param
        return url

    def scrape(self) -> None:
        """Main scraping method to collect property IDs."""

        # Automatically closes driver after use
        with self.get_driver() as driver:
            self.warmup_driver(driver, self.settings.base_url)

            # Navigate to the initial page
            full_scrape_url = self._get_url_with_params(self.settings, self.scrape_url)
            self.logger.info("Navigating to scrape URL: %s", full_scrape_url)
            self.get_page(driver, full_scrape_url)

            total_listings = 0
            total_inserted = 0
            while True:
                page_n = self._get_current_page_number(driver)
                self.logger.info(f"Scraping page {page_n}...")

                # Random scroll before scraping
                driver.execute_script(f"window.scrollTo(0, {random.randint(100, 300)});")
                self._realistic_wait()

                # Find all listing content containers
                content_elements: list[WebElement] = driver.find_elements(By.CSS_SELECTOR, "div.styles_in-listingCardPropertyContent__tfu8w")
                self.logger.info("Found %d listings", len(content_elements))

                listings = []
                for i, content_element in enumerate(content_elements):
                    try:
                        # Find the link within the content container
                        link_element = content_element.find_element(By.CSS_SELECTOR, "a[href*='immobiliare.it/annunci']")
                        link = link_element.get_attribute("href")
                        if not link:
                            self.logger.warning("Listing without link found, skipping")
                            continue

                        title = link_element.get_attribute("title") or link_element.text.strip()
                        if not title:
                            self.logger.warning("Listing without title found, skipping")
                            continue
                        source_id = ImmobiliareIdScraper.extract_listing_id(link)
                        if not source_id:
                            self.logger.warning("Could not extract ID from link: %s", link)
                            continue

                        # Validate resolved ID
                        if self._is_auction(content_element):
                            self.logger.warning("Skipping auction listing [%s]", link)
                            continue

                        id = ListingId(source=SOURCE, source_id=source_id, title=title, url=link)
                        listings.append(id)

                    except Exception as e:
                        self.logger.warning(f"Error processing listing: {e}")
                        continue

                # Salva progressivo
                self.logger.info("Going to attempt storage of %d listings", len(listings))
                inserted_count = self.storage.append_data(listings)

                total_listings += len(listings)
                total_inserted += inserted_count
                self.logger.info("Listings scraped: [%d]. Listings inserted: [%d]", total_listings, total_inserted)

                # Stop condition
                if total_listings >= self.settings.listing_limit:
                    self.logger.info("Reached the maximum number of [%d] listings, stopping", self.settings.listing_limit)
                    break
                if page_n >= self.settings.max_pages:
                    self.logger.info("Reached the maximum number of [%d] pages, stopping", self.settings.max_pages)
                    break

                # Random pause between pages
                self._realistic_wait()
                self.scroll_to_bottom(driver)

                is_next = self.to_next_page(driver, page_n)
                if not is_next:
                    self.logger.error("No more pages to scrape or button not found.")
                    break

            self.logger.info("Done! Total listing IDs scraped: %d", total_listings)

    def _is_auction(self, content_element) -> bool:
        """Check if a listing has auction/variable pricing.
        
        Args:
            content_element: WebElement representing the content container
            
        Returns:
            bool: True if listing has auction pricing, False otherwise
        """
        try:
            element_text = content_element.text.lower()
            return "da €" in element_text
        except Exception:
            return False

    @staticmethod
    def extract_listing_id(url: str) -> str | None:
        """Extract numerical ID from immobiliare.it listing URL.
        
        Args:
            url: URL in format "https://www.immobiliare.it/annunci/{id}/"
            
        Returns:
            Numerical ID as string, or None if not found
        """
        import re

        # Pattern to match the numerical ID between /annunci/ and the final /
        pattern = r'/annunci/(\d+)/?$'
        match = re.search(pattern, url.strip())

        return match.group(1) if match else None

    def to_next_page(self, driver, current_page: int) -> bool:
        """Navigate to the next page of listings."""
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, f'a[href*="pag={current_page + 1}"]')
            if not (next_btn.is_enabled() and next_btn.is_displayed()):
                self.logger.error("Button 'Prossima pagina' non enabled or not displayed")
                return False

            if next_btn:
                # Scroll to button and click with human-like behavior
                self.logger.info("Button 'Prossima pagina' found, navigating to next page")
                driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                self._realistic_wait()

                # Use ActionChains for more natural clicking
                actions = ActionChains(driver)
                actions.move_to_element(next_btn).pause(
                    random.uniform(0.5, 1.5)
                ).click().perform()

                self.logger.info("Clicked on 'Prossima pagina' button!")
                # Wait for page to load
                self._realistic_wait()
                return True
            else:
                self.logger.error("No more pages or button not found.")
                return False

        except Exception as e:
            self.logger.error(f"Navigation error: {e}")
            return False

    def _get_current_page_number(self, driver) -> int:
        """Extract current page number from URL.

        Args:
            driver: WebDriver instance

        Returns:
            Current page number (1 if no pag= parameter found)
        """
        current_url = driver.current_url
        self.logger.debug("Current URL: %s", current_url)

        # Look for pag= parameter in URL
        match = re.search(r"pag=(\d+)", current_url)

        if match:
            page_number = int(match.group(1))
            self.logger.debug("Extracted page number from URL: %d", page_number)
            return page_number
        else:
            self.logger.debug("No pag= parameter found in URL, assuming page 1")
            return 1
