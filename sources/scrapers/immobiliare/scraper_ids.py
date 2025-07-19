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

class ImmobiliareIdScraper(SeleniumScraper):
    """Scraper for Immobiliare.it using Selenium."""

    def __init__(self, 
                 storage: Storage, 
                 base_url: str = "https://www.immobiliare.it/",
                 **kwargs):
        """Initialize the Immobiliare scraper with specific settings."""
        super().__init__(storage, base_url, **kwargs)

    def scrape(self):
        """Main scraping method to collect property IDs."""

        # Automatically closes driver after use
        with self.get_driver() as driver:
            self.warmup_driver(driver)

            # Human-like behavior: scroll and wait
            driver.execute_script("window.scrollTo(0, 0);")

            pagina = 1
            total_listings = 0
            while True:
                logger.info(f"Scraping page {pagina}...")

                # Random scroll before scraping
                driver.execute_script(f"window.scrollTo(0, {random.randint(100, 300)});")
                self._realistic_wait()

                # Trova tutti i <a> con classe dei titoli
                listings = driver.find_elements(By.CSS_SELECTOR, "a[href*='immobiliare.it/annunci']")
                logger.info("Found %d listings", len(listings))

                listings = []
                for i, listing in enumerate(listings):
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

                        id = ListingId(source=Source.IMMOBILIARE, source_id=source_id, title=title, url=link)
                        listings.append(id)

                        # Simulate human reading time
                        # if i % 5 == 0:
                        #    time.sleep(random.uniform(0.5, 1.5))
                    except Exception as e:
                        print(f"Errore processando annuncio: {e}")
                        continue

                logger.info("New listings added: %d", len(listings)) 

                # Salva progressivo
                self.storage.append_data(listings)
                total_listings += len(listings)

                # Random pause between pages
                self._realistic_wait()
                self.scroll_to_bottom(driver)

                # Cerca bottone per andare alla prossima pagina
                try:
                    next_btn = driver.find_element(By.CSS_SELECTOR, f'a[href*="pag={pagina + 1}"]')
                    time.sleep(random.uniform(1, 2))
                    if not (next_btn.is_enabled() and next_btn.is_displayed()):
                        print("Button 'Prossima pagina' non enabled or not displayed")
                        break

                    if next_btn:
                        # Scroll to button and click with human-like behavior
                        print("Trovato pulsante 'Prossima pagina'")
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                        time.sleep(random.uniform(1, 2))

                        # Use ActionChains for more natural clicking
                        actions = ActionChains(driver)
                        actions.move_to_element(next_btn).pause(
                            random.uniform(0.5, 1.5)
                        ).click().perform()

                        # Wait for page to load
                        time.sleep(random.uniform(4, 8))
                        pagina += 1
                    else:
                        print("Fine pagine o pulsante non trovato.")
                        break

                except Exception as e:
                    print(f"Errore navigazione: {e}")
                    break

                # Fai stop se hai già tanti annunci

                if total_listings >= 3000:
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

# uv run --env-file sources/resources/config.dev.env sources/scrapers/immobiliare/scraper_ids.py
if __name__ == "__main__":  
    logging_utils.setup_logging(config_path='sources/resources/logging.yaml')
    storage: Storage = FileStorage(ListingId, CsvStorageSettings())
    scraper = ImmobiliareIdScraper(storage)
    scraper.scrape()
