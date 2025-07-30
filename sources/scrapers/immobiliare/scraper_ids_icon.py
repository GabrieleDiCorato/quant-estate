import time
import random
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

# Mappatura hashtag -> id nel markup
FEATURES = {
    "#palaces": "palaces",
    "#money": "money",
    "#size": "size",
    "#planimetry": "planimetry",
    "#bath": "bath",
    "#stairs": "stairs",
    "#beach-umbrella": "beach-umbrella",
    "#tree": "tree",
    "#garage": "garage",
    "#fire": "fire",
    "#helmet": "helmet",
    "#certificate": "certificate",
    "#building": "building",
    "#elevator": "elevator",
    "#bed": "bed",
    "#kitchen": "kitchen",
    "#balcony": "balcony",
    "#shelf": "shelf",
    "#calendar": "calendar",
    "#disabled": "disabled",
    "#diamond": "diamond",
    "#couch-lamp": "couch-lamp",
    "#unlock": "unlock",
    "#reception": "reception",
    "#air-conditioning": "air-conditioning",
    "#leaf": "leaf",
    "#euro-circle": "euro-circle",
    "#chart": "chart"
}

def realistic_wait(min_delay=1.0, max_delay=3.0, long_pause_chance=0.05):
    base = random.uniform(min_delay, max_delay)
    jitter = random.uniform(-0.2, 0.3)
    extra = random.uniform(1.0, 3.0) if random.random() < long_pause_chance else 0.0
    time.sleep(max(0, base + jitter + extra))

def main(input_csv='milano_links.csv', output_csv='dati_ann.csv', headless=False):
    # Leggi i primi 20 link
    df = pd.read_csv(input_csv).head(20)
    results = []

    # Setup Chrome
    options = uc.ChromeOptions()
    for arg in [
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--allow-running-insecure-content",
        "--start-maximized",
        "--no-sandbox",
        "--disable-setuid-sandbox"
    ]:
        options.add_argument(arg)
    if headless:
        options.add_argument("--headless=new")

    driver = uc.Chrome(options=options)
    driver.implicitly_wait(10)
    wait = WebDriverWait(driver, 10)

    for _, row in df.iterrows():
        link = row.get('link_annuncio', row.get('link'))
        data = {'link': link}
        try:
            driver.get(link)
            realistic_wait()

            # Trova e clicca il pulsante per aprire il dialog
            try:
                btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH,
                     "//button[contains(@class,'openDialogButton') and normalize-space(.)='Vedi tutte le caratteristiche']")
                ))
            except TimeoutException:
                print(f"Nessun pulsante caratteristiche su {link}, salto")
                for tag in FEATURES:
                    data[tag] = None
                results.append(data)
                continue

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            realistic_wait(0.5, 1.0)
            btn.click()

            # Attendi che il dialog sia visibile
            try:
                dialog = wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'section[class*="DialogSection"]'))
                )
            except TimeoutException:
                print(f"Dialog non apparso su {link}, chiudo e proseguo")
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                realistic_wait()
                for tag in FEATURES:
                    data[tag] = None
                results.append(data)
                continue

            realistic_wait()

            # Scrolla il container del dialog fino in fondo per caricare tutte le icone
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", dialog)
            realistic_wait(0.5, 1.0)

            # Estrai ciascuna feature: scrolla ogni icona nel view e prendi il <dd>
            for tag, id_val in FEATURES.items():
                try:
                    icon_sel = f'use.nd-icon__use[href="#' + id_val + '"]'
                    icon = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, icon_sel)))
                    # scrolla l'icona nel container
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", icon)
                    realistic_wait(0.2, 0.5)
                    dd = icon.find_element(By.XPATH, 'ancestor::dt/following-sibling::dd')
                    data[tag] = dd.text.strip()
                except Exception:
                    data[tag] = None

            # Chiudi il dialog
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            wait.until(EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, 'section[class*="DialogSection"]')
            ))
            realistic_wait()

        except Exception as e:
            print(f"Errore su {link}: {e}")
        results.append(data)

    # Salva CSV
    pd.DataFrame(results).to_csv(output_csv, index=False)
    print(f"Salvati {len(results)} righe in {output_csv}")

if __name__ == '__main__':
    main(headless=False)
