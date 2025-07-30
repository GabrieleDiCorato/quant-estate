import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import random

from sources.config.model.storage_settings import CsvStorageSettings
from sources.datamodel.enumerations import Source
from sources.datamodel.listing_id import ListingId
from sources.logging import logging_utils
from sources.scrapers.selenium_scraper import SeleniumScraper
from sources.storage.abstract_storage import Storage
from sources.storage.file_storage import FileStorage

logger = logging.getLogger(__name__)
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

    def scrape(self):
        """Main scraping method to collect property IDs."""

        # Automatically closes driver after use
        with self.get_driver() as driver:
            self.warmup_driver(driver)

            # Navigate to the initial page
            logger.info("Navigating to scrape URL: %s", self.scrape_url)
            self.get_page(driver, self.scrape_url)
            page_n = 1
            total_listings = 0
            while True:
                logger.info(f"Scraping page {page_n}...")

                # Random scroll before scraping
                driver.execute_script(f"window.scrollTo(0, {random.randint(100, 300)});")
                self._realistic_wait()

                # Find all listing elements
                elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='immobiliare.it/annunci']")
                logger.info("Found %d listings", len(elements))

                listings = []
                for i, listing in enumerate(elements):
                    try:
                        link = listing.get_attribute("href")
                        if not link:
                            logger.warning("Listing without link found, skipping")
                            continue
                        title = listing.get_attribute("title") or listing.text.strip()
                        if not title:
                            logger.warning("Listing without title found, skipping")
                            continue
                        source_id = ImmobiliareIdScraper.extract_listing_id(link)
                        if not source_id:
                            logger.warning("Could not extract ID from link: %s", link)
                            continue

                        id = ListingId(source=SOURCE, source_id=source_id, title=title, url=link)
                        listings.append(id)

                    except Exception as e:
                        print(f"Errore processando annuncio: {e}")
                        continue

                total_listings += len(listings)
                logger.info("New listings found: [%d]. Total: [%d]", len(listings), total_listings)

                # Salva progressivo
                self.storage.append_data(listings)

                # Random pause between pages
                self._realistic_wait()
                self.scroll_to_bottom(driver)

                is_next = self.to_next_page(driver, page_n)
                if not is_next:
                    logger.error("No more pages to scrape or button not found.")
                    break

                page_n += 1

                # Fai stop se hai già tanti annunci
                if total_listings >= 3000 or page_n == 80:
                    print("Raggiunti 3000 annunci, stop.")
                    break

            print("Fatto! Totale annunci raccolti:", total_listings)

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
                logger.error("Button 'Prossima pagina' non enabled or not displayed")
                return False

            if next_btn:
                # Scroll to button and click with human-like behavior
                logger.info("Button 'Prossima pagina' found, navigating to next page")
                driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                self._realistic_wait()

                # Use ActionChains for more natural clicking
                actions = ActionChains(driver)
                actions.move_to_element(next_btn).pause(
                    random.uniform(0.5, 1.5)
                ).click().perform()

                logger.info("Clicked on 'Prossima pagina' button!")
                # Wait for page to load
                self._realistic_wait()
                return True
            else:
                logger.error("No more pages or button not found.")
                return False

        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False


# uv run --env-file sources/resources/config.dev.env sources/scrapers/immobiliare/scraper_ids.py
if __name__ == "__main__":  
    logging_utils.setup_logging(config_path='sources/resources/logging.yaml')
    storage: Storage = FileStorage(ListingId, CsvStorageSettings())
    scraper = ImmobiliareIdScraper(
        storage,
        scrape_url="https://www.immobiliare.it/vendita-case/milano/?criterio=data&ordine=desc"
    )
    scraper.scrape()
