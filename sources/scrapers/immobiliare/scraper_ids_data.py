import logging
import time
import random
import argparse
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class AnnuncioInfoScraper:
    """Scraper using undetected-chromedriver and realistic waits for multiple fields extraction."""

    def __init__(
        self,
        headless: bool = True,
        implicit_wait: int = 10,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        long_pause_chance: float = 0.05,
        long_pause_range: tuple = (1.0, 3.0)
    ):
        options = uc.ChromeOptions()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--start-maximized")
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")

        self.driver = uc.Chrome(options=options)
        self.driver.implicitly_wait(implicit_wait)
        self.implicit_wait = implicit_wait
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.long_pause_chance = long_pause_chance
        self.long_pause_range = long_pause_range

        logger.info("Initialized undetected-chromedriver with headless=%s", headless)

    def _realistic_wait(self):
        base = random.uniform(self.min_delay, self.max_delay)
        jitter = random.uniform(-0.2, 0.3)
        extra = random.uniform(*self.long_pause_range) if random.random() < self.long_pause_chance else 0.0
        delay = max(0, base + jitter + extra)
        logger.debug("Waiting %.2f seconds", delay)
        time.sleep(delay)

    def scrape(self, input_csv: str, output_csv: str):
        df = pd.read_csv(input_csv)
        if 'link_annuncio' not in df.columns:
            logger.error("CSV deve contenere la colonna 'link_annuncio'")
            return

        # take only first 20
        df = df.head(30)
        results = []

        for _, row in df.iterrows():
            url = row['link_annuncio']
            data = {'link_annuncio': url}
            try:
                self.driver.get(url)
                self._realistic_wait()
                wait = WebDriverWait(self.driver, self.implicit_wait)

                # estrazione prezzo
                price_elem = wait.until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        "div.Price_price__mzj0D.styles_ld-overview__price__QSGQc span"
                    ))
                )
                price_text = price_elem.text.strip()
                digits = price_text.replace('€', '').replace('.', '').replace(' ', '')
                price_eur = float(digits)
                data['price_text'] = price_text
                data['price_eur'] = price_eur

                self._realistic_wait()

                # riferimento_annuncio
                ref_el = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                        "p.styles_ld-descriptionHeading__reference__M9PV6"))
                )
                ref_text = ref_el.text.strip()
                data['riferimento_annuncio'] = ref_text.split(':')[-1].strip()

                self._realistic_wait()

                # classe_energetica
                ce_el = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                        "span.styles_ld-energyMainConsumptions__consumptionColorClass__o4IZg.styles_ld-energyRating__aCjct"))
                )
                data['classe_energetica'] = ce_el.get_attribute('data-energy-class') or ce_el.text.strip()

                self._realistic_wait()

                # descrizione
                desc_el = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                        "div.styles_in-readAll__04LDT > div"))
                )
                data['descrizione'] = desc_el.text.strip()

                logger.info("Estratti campi per %s", url)
                self._realistic_wait()

            except Exception as e:
                logger.error("Errore su %s: %s", url, e)
                data.update({
                    'price_text': None,
                    'price_eur': None,
                    'riferimento_annuncio': None,
                    'classe_energetica': None,
                    'descrizione': None,
                    'error': str(e)
                })

            results.append(data)

        pd.DataFrame(results).to_csv(output_csv, index=False)
        logger.info("Salvati %d righe in %s", len(results), output_csv)

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Estrai info e prezzo da 5 annunci di Immobiliare.it")
    parser.add_argument('--input_csv', default='milano_links.csv', help="CSV con 'link_annuncio'")
    parser.add_argument('--output_csv', default='annunci_info.csv', help="CSV di output con campi aggiuntivi")
    parser.add_argument('--headless', action='store_true', help="Headless mode")
    args = parser.parse_args()

    scraper = AnnuncioInfoScraper(headless=args.headless)
    try:
        scraper.scrape(args.input_csv, args.output_csv)
    finally:
        scraper.close()
