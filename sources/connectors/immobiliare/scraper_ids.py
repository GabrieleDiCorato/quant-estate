import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
import time
import random
import pandas as pd
import os

logger = logging.getLogger(__name__)

# Anti-detection Chrome config
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--allow-running-insecure-content")
chrome_options.add_argument("--disable-features=VizDisplayCompositor")
chrome_options.add_argument("--window-size=1366,768")

# Realistic user agents
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
]
user_agent = random.choice(user_agents)
chrome_options.add_argument(f'--user-agent={user_agent}')

driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()), options=chrome_options
)

# Execute stealth script
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
driver.execute_cdp_cmd('Network.setUserAgentOverride', {
    "userAgent": user_agent,
    "acceptLanguage": "en-US,en;q=0.9",
    "platform": "Win32"
})


# prova
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
driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
time.sleep(random.uniform(2, 4))
driver.execute_script("window.scrollTo(0, 0);")
time.sleep(random.uniform(2, 3))

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
    time.sleep(random.uniform(3, 7))

    # Cerca bottone per andare alla prossima pagina
    try:
        # Try multiple selectors for next button
        next_selectors = [
            'a[aria-label="Pagina successiva"]',
            'a[title="Pagina successiva"]',
            '.pagination__next',
            'a:contains("Successiva")',
            'a[href*="pag="]'
        ]
        
        next_btn = None
        for selector in next_selectors:
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, selector)
                if next_btn.is_enabled() and next_btn.is_displayed():
                    break
            except:
                continue
                
        if next_btn:
            # Scroll to button and click with human-like behavior
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
        
    # Break if no new listings found (might indicate blocking)
    if nuovi_annunci == 0:
        print("Nessun nuovo annuncio trovato, possibile blocco.")
        break

driver.quit()
print("Fatto! Totale annunci raccolti:", len(links_raccolti))
