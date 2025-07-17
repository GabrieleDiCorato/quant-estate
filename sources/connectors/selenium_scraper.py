"""
Selenium-based web scraper base class.
"""

import logging
import random
import time
from abc import ABC, abstractmethod
from typing import Any, Optional
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, NoSuchElementException
)
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from ..exceptions import ConfigurationError, ScrapingError
from ..datamodel.listing_details import ListingDetails

logger = logging.getLogger(__name__)


class SeleniumScraper(ABC):
    """Abstract base class for Selenium-based web scrapers."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the scraper with configuration.

        Args:
            config: Configuration dictionary

        Raises:
            ConfigurationError: If required configuration keys are missing
        """
        try:
            self.config = config
            self.base_url = config['base_url']
            self.min_delay = config['request_settings']['min_delay']
            self.max_delay = config['request_settings']['max_delay']
            
            # Selenium-specific settings
            self.browser = config.get('browser', 'chrome').lower()
            self.headless = config.get('headless', True)
            self.implicit_wait = config.get('implicit_wait', 10)
            self.page_load_timeout = config.get('page_load_timeout', 30)
            
            # User agent settings
            self.user_agents = config.get('user_agents', [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ])
            
            logger.info("Initialized SeleniumScraper with browser: %s, headless: %s", 
                       self.browser, self.headless)

        except KeyError as e:
            raise ConfigurationError(f"Missing required configuration key: {e}")

    def _create_driver(self) -> WebDriver:
        """Create and configure a WebDriver instance.
        
        Returns:
            WebDriver: Configured WebDriver instance
            
        Raises:
            ConfigurationError: If browser configuration is invalid
            ScrapingError: If WebDriver creation fails
        """
        try:
            if self.browser == 'chrome':
                options = ChromeOptions()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                # Random user agent
                user_agent = random.choice(self.user_agents)
                options.add_argument(f'--user-agent={user_agent}')
                
                driver = webdriver.Chrome(
                    service=ChromeService(ChromeDriverManager().install()),
                    options=options
                )
                
            elif self.browser == 'firefox':
                options = FirefoxOptions()
                if self.headless:
                    options.add_argument('--headless')
                
                # Random user agent
                user_agent = random.choice(self.user_agents)
                options.set_preference("general.useragent.override", user_agent)
                
                driver = webdriver.Firefox(
                    service=FirefoxService(GeckoDriverManager().install()),
                    options=options
                )
            else:
                raise ConfigurationError(f"Unsupported browser: {self.browser}")
            
            # Configure timeouts
            driver.implicitly_wait(self.implicit_wait)
            driver.set_page_load_timeout(self.page_load_timeout)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Created WebDriver instance: %s", self.browser)
            return driver
            
        except Exception as e:
            logger.error("Failed to create WebDriver: %s", str(e), exc_info=True)
            raise ScrapingError(f"Failed to create WebDriver: {e}")

    @contextmanager
    def get_driver(self):
        """Context manager for WebDriver with proper cleanup.
        
        Yields:
            WebDriver: Configured WebDriver instance
        """
        driver = self._create_driver()
        try:
            yield driver
        finally:
            try:
                driver.quit()
                logger.debug("WebDriver session closed")
            except Exception as e:
                logger.warning("Error closing WebDriver: %s", str(e))

    def get_page(self, driver: WebDriver, url: str, wait_for_element: Optional[tuple[str, str]] = None) -> None:
        """Navigate to a page and optionally wait for an element.

        Args:
            driver: WebDriver instance
            url: URL to navigate to
            wait_for_element: Optional tuple of (By, locator) to wait for

        Raises:
            ScrapingError: If there's an error loading the page
        """
        try:
            # Add random delay
            delay = random.uniform(self.min_delay, self.max_delay)
            logger.debug("Waiting %.2f seconds before request", delay)
            time.sleep(delay)
            
            logger.debug("Navigating to: %s", url)
            driver.get(url)
            
            # Wait for specific element if provided
            if wait_for_element:
                by_str, locator = wait_for_element
                by = getattr(By, by_str.upper())
                WebDriverWait(driver, self.implicit_wait).until(
                    EC.presence_of_element_located((by, locator))
                )
                logger.debug("Found expected element: %s", locator)
            
        except TimeoutException as e:
            logger.error("Timeout loading page %s: %s", url, str(e))
            raise ScrapingError(f"Timeout loading page: {e}")
        except WebDriverException as e:
            logger.error("WebDriver error loading page %s: %s", url, str(e))
            raise ScrapingError(f"WebDriver error: {e}")
        except Exception as e:
            logger.error("Unexpected error loading page %s: %s", url, str(e), exc_info=True)
            raise ScrapingError(f"Unexpected error loading page: {e}")

    def wait_for_element(self, driver: WebDriver, by: str, locator: str, timeout: int = 10):
        """Wait for an element to be present on the page.
        
        Args:
            driver: WebDriver instance
            by: Selenium By locator type as string (e.g., 'id', 'class_name', 'xpath')
            locator: Element locator string
            timeout: Timeout in seconds
            
        Returns:
            WebElement: The found element
            
        Raises:
            ScrapingError: If element is not found within timeout
        """
        try:
            by_obj = getattr(By, by.upper())
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by_obj, locator))
            )
            return element
        except TimeoutException:
            logger.error("Element not found: %s=%s", by, locator)
            raise ScrapingError(f"Element not found: {by}={locator}")

    def scroll_to_bottom(self, driver: WebDriver, pause_time: float = 1.0) -> None:
        """Scroll to the bottom of the page to load dynamic content.
        
        Args:
            driver: WebDriver instance
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
            
        logger.debug("Scrolled to bottom of page")

    @abstractmethod
    def validate_url(self, url: str) -> None:
        """Validate that the URL is appropriate for this scraper.
        
        Args:
            url: URL to validate
            
        Raises:
            ValidationError: If the URL is invalid
        """
        pass

    @abstractmethod
    def scrape_listings(self, url: str) -> list[ListingDetails]:
        """Scrape listings from the given URL.
        
        Args:
            url: URL to scrape listings from
            
        Returns:
            List of ListingDetails objects
            
        Raises:
            ScrapingError: If there's an error scraping the listings
        """
        pass
