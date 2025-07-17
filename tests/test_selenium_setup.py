"""
Test script to verify Selenium setup for immobiliare.it scraping.
"""

import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_selenium_setup():
    """Test Selenium setup with immobiliare.it scraper."""
    try:
        # Test direct selenium import
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Test WebDriver creation
        options = ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )
        
        logger.info("✅ WebDriver created successfully")
        
        # Test navigation to a simple page
        driver.get("https://www.immobiliare.it")
        logger.info("✅ Successfully navigated to immobiliare.it")
        
        # Test basic page interaction
        title = driver.title
        logger.info("✅ Page title: %s", title)
        
        # Clean up
        driver.quit()
        logger.info("✅ WebDriver closed successfully")
        
        logger.info("✅ Selenium setup test completed successfully!")
        return True
        
    except Exception as e:
        logger.error("❌ Selenium setup test failed: %s", str(e), exc_info=True)
        return False

if __name__ == "__main__":
    success = test_selenium_setup()
    sys.exit(0 if success else 1)
