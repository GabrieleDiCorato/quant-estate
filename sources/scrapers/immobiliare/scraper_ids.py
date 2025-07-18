import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from undetected_chromedriver import Chrome, ChromeOptions
import time
import random
import pandas as pd
import os

logger = logging.getLogger(__name__)


def scroll_to_bottom(driver: Chrome, pause_time: float = 1.0) -> None:
    """Scroll to the bottom of the page to load dynamic content.

    Args:
        driver: Undetected Chrome instance
        pause_time: Time to pause between scrolls
    """
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for new content to load
        time.sleep(pause_time)

        # Check if we've reached the bottom
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    print("Scrolled to bottom of page")


# Anti-detection Chrome config
chrome_options = ChromeOptions()
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--allow-running-insecure-content")
chrome_options.add_argument("--window-size=1366,768")
# Don't set user agent manually - undetected_chromedriver handles this

# Instantiate a Chrome browser with correct parameters
driver = Chrome(options=chrome_options, version_main=None)

# Resume: carica se esiste
file_csv = "milano_links.csv"
if os.path.exists(file_csv):
    df = pd.read_csv(file_csv)
    links_raccolti = set(df['link_annuncio'].tolist())
else:
    df = pd.DataFrame(columns=['titolo_annuncio', 'link_annuncio'])
    links_raccolti = set()

# Vai alla prima pagina
url_base = "https://www.immobiliare.it/vendita-case/milano/?criterio=data&ordine=desc"
driver.get(url_base)

# Human-like behavior: scroll and wait
time.sleep(random.uniform(3, 6))
driver.execute_script("window.scrollTo(0, 0);")

# Try to dismiss any cookie banners or popups
try:
    wait = WebDriverWait(driver, 5)
    accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accetta') or contains(text(), 'Accept') or contains(@id, 'accept')]")))
    accept_btn.click()
    time.sleep(random.uniform(1, 2))
except:
    pass

pagina = 1
while True:
    print(f"Pagina {pagina}")

    # Random scroll before scraping
    driver.execute_script(f"window.scrollTo(0, {random.randint(100, 300)});")
    time.sleep(random.uniform(1, 2))

    # Trova tutti i <a> con classe dei titoli
    annunci = driver.find_elements(By.CSS_SELECTOR, "a[href*='immobiliare.it/annunci']")
    print("Trovati annunci:", len(annunci))
    nuovi_annunci = 0

    for i, annuncio in enumerate(annunci):
        try:
            link = annuncio.get_attribute("href")
            titolo = annuncio.get_attribute("title") or annuncio.text.strip()

            if link and link not in links_raccolti:
                new_row = pd.DataFrame({'titolo_annuncio': [titolo], 'link_annuncio': [link]})
                df = pd.concat([df, new_row], ignore_index=True)
                links_raccolti.add(link)
                nuovi_annunci += 1

            # Simulate human reading time
            if i % 5 == 0:
                time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            print(f"Errore processando annuncio: {e}")
            continue

    print(f"Nuovi annunci aggiunti: {nuovi_annunci}")

    # Salva progressivo
    df.to_csv(file_csv, index=False)

    # Random pause between pages
    time.sleep(random.uniform(1, 2))

    scroll_to_bottom(driver=driver)

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
            actions.move_to_element(next_btn).pause(random.uniform(0.5, 1.5)).click().perform()

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
    if len(links_raccolti) >= 3000:
        print("Raggiunti 3000 annunci, stop.")
        break

driver.quit()
print("Fatto! Totale annunci raccolti:", len(links_raccolti))
