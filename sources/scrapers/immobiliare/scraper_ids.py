import logging
import re
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from sources.config.model.storage_settings import CsvStorageSettings
from sources.datamodel.listing_id import ListingId
from sources.logging import logging_utils
from sources.scrapers.selenium_scraper import SeleniumScraper
from sources.storage.abstract_storage import Storage
from sources.storage.file_storage import FileStorage

SOURCE = "immobiliare"

class ImmobiliareIdScraper(SeleniumScraper):
    """Scraper for Immobiliare.it using Selenium."""

    def __init__(self, 
                 storage: Storage, 
                 base_url: str = "https://www.immobiliare.it/",
                 scrape_url: str = "https://www.immobiliare.it/vendita-case/milano/?criterio=data&ordine=desc",
                 **kwargs):
        """Initialize the Immobiliare scraper with specific settings."""
        super().__init__(storage, base_url, scrape_url=scrape_url, **kwargs)

        # Create instance-specific logger
        self.logger = logging.getLogger(f"{__name__}.{self._instance_id}")

    def scrape(self, limit: int = 2000):
        """Main scraping method to collect property IDs."""

        # Automatically closes driver after use
        with self.get_driver() as driver:
            self.warmup_driver(driver)

            # Navigate to the initial page
            self.logger.info("Navigating to scrape URL: %s", self.scrape_url)
            self.get_page(driver, self.scrape_url)

            total_listings = 0
            total_inserted = 0
            while True:
                page_n = self._get_current_page_number(driver)
                self.logger.info(f"Scraping page {page_n}...")

                # Random scroll before scraping
                driver.execute_script(f"window.scrollTo(0, {random.randint(100, 300)});")
                self._realistic_wait()

                # Find all listing elements
                elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='immobiliare.it/annunci']")
                self.logger.info("Found %d listings", len(elements))

                listings = []
                for i, listing in enumerate(elements):
                    try:
                        link = listing.get_attribute("href")
                        if not link:
                            self.logger.warning("Listing without link found, skipping")
                            continue
                        title = listing.get_attribute("title") or listing.text.strip()
                        if not title:
                            self.logger.warning("Listing without title found, skipping")
                            continue
                        source_id = ImmobiliareIdScraper.extract_listing_id(link)
                        if not source_id:
                            self.logger.warning("Could not extract ID from link: %s", link)
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

                # Random pause between pages
                self._realistic_wait()
                self.scroll_to_bottom(driver)

                is_next = self.to_next_page(driver, page_n)
                if not is_next:
                    self.logger.error("No more pages to scrape or button not found.")
                    break

                # Stop condition
                if total_listings >= limit or page_n == 80:
                    self.logger.info("Raggiunti %d annunci, stop.", limit)
                    break

            self.logger.info("Done! Total listing IDs scraped: %d", total_listings)

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


# uv run --env-file sources/resources/config.dev.env sources/scrapers/immobiliare/scraper_ids.py
# See im_pipeline_ids.ipynb for a more interactive usage and extensive configuration using env variables and config files.
if __name__ == "__main__":  
    logging_utils.setup_logging(config_path="sources/resources/logging.yaml")

    storage: Storage = FileStorage(ListingId, CsvStorageSettings())
    scraper = ImmobiliareIdScraper(
        storage,
        scrape_url="https://www.immobiliare.it/vendita-case/milano/?criterio=data&ordine=desc"
    )
    scraper.scrape()
