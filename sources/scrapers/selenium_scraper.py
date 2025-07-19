"""
Selenium-based web scraper base class using undetected-chromedriver.
"""

import logging
import random
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import undetected_chromedriver as uc

from sources.storage.abstract_storage import Storage

from ..exceptions import ConfigurationError, ScrapingError
from ..datamodel.listing_details import ListingDetails

logger = logging.getLogger(__name__)

class SeleniumScraper(ABC):
    """Abstract base class for Selenium-based web scrapers."""

    def __init__(
        self,
        storage: Storage,
        base_url: str,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        headless: bool = False,
        implicit_wait: int = 10,
        page_load_timeout: int = 30,
        window_size: tuple[int, int] = (1366, 768),
    ):
        """Initialize the scraper with configuration.

        Args:
            config: Configuration dictionary

        Raises:
            ConfigurationError: If required configuration keys are missing
        """
        try:
            self.storage = storage
            self.base_url = base_url
            self.min_delay = min_delay
            self.max_delay = max_delay

            # Undetected Chrome settings
            self.headless = headless
            self.implicit_wait = implicit_wait
            self.page_load_timeout = page_load_timeout
            self.window_size = window_size

            logger.info("Initialized SeleniumScraper with headless: %s", self.headless)

        except KeyError as e:
            raise ConfigurationError(f"Missing required configuration key: {e}")

    def _create_driver(self) -> uc.Chrome:
        """Create and configure an undetected Chrome WebDriver instance.
        
        Returns:
            uc.Chrome: Configured undetected Chrome instance
            
        Raises:
            ScrapingError: If WebDriver creation fails
        """
        try:
            # Configure Chrome options
            options = uc.ChromeOptions()

            # Essential options only - let undetected-chromedriver handle stealth
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            # options.add_argument(f"--window-size={self.window_size[0]},{self.window_size[1]}")
            options.add_argument("--start-maximized")

            if self.headless:
                options.add_argument("--headless=new")  # Use new headless mode

            # Create undetected Chrome driver
            driver = uc.Chrome(
                options=options,
                version_main=None,  # Auto-detect Chrome version
                driver_executable_path=None,  # Auto-download if needed
                browser_executable_path=None  # Use system Chrome
            )

            # Configure timeouts
            driver.implicitly_wait(self.implicit_wait)
            driver.set_page_load_timeout(self.page_load_timeout)

            logger.info("Created undetected Chrome WebDriver instance")
            return driver

        except Exception as e:
            logger.error("Failed to create undetected Chrome WebDriver: %s", str(e), exc_info=True)
            raise ScrapingError(f"Failed to create WebDriver: {e}")

    @contextmanager
    def get_driver(self):
        """Context manager for WebDriver with proper cleanup.
        
        Yields:
            uc.Chrome: Configured undetected Chrome instance
        """
        driver = self._create_driver()
        try:
            yield driver
        finally:
            try:
                driver.quit()
                logger.info("WebDriver session closed")
            except Exception as e:
                logger.warning("Error closing WebDriver: %s", str(e))

    def warmup_driver(self, driver):
        # Visit the homepage to get cookies
        logger.info("Visiting homepage to initialize session...")
        self.get_page(driver, self.base_url)
        # Wait for the manual captcha solving or any initial loading
        time.sleep(10)  
        self._realistic_wait()
        self._close_cookies(driver)
        self._realistic_wait()
        logger.info("Session is warmed up!")

    def get_page(self, driver: uc.Chrome, url: str, wait_for_element: tuple[str, str] | None = None) -> None:
        """Navigate to a page and optionally wait for an element.

        Args:
            driver: WebDriver instance
            url: URL to navigate to
            wait_for_element: Optional tuple of (By, locator) to wait for

        Raises:
            ScrapingError: If there's an error loading the page
        """
        try:
            logger.info("Navigating to: %s", url)
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

    def scroll_to_bottom(self, driver: uc.Chrome, pause_time: float = 1.0) -> None:
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

        logger.debug("Scrolled to bottom of page")

    def _realistic_wait(self) -> None:
        """Wait with realistic randomization to mimic human behavior."""
        # Generate base delay
        base_delay = random.uniform(self.min_delay, self.max_delay)
        jitter_delay = random.uniform(-0.2, 0.3)
        # Occasionally add longer pauses (5% chance) to simulate human distractions
        extra_pause = 0.0 if random.random() >= 0.05 else random.uniform(1.0, 3.0)
        delay = base_delay + jitter_delay + extra_pause

        logger.debug("Realistic wait: %.2f seconds", delay)
        time.sleep(delay)

    def _close_cookies(self, driver: uc.Chrome) -> None:
        """Close the cookies banner if present.

        Args:
            driver: WebDriver instance
        """
        # Try to dismiss any cookie banners or popups
        try:
            wait = WebDriverWait(driver, 5)
            accept_btn = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(text(), 'Accetta') or contains(text(), 'Accept') or contains(@id, 'accept')]",
                    )
                )
            )
            accept_btn.click()
        except Exception as e:
            logger.warning("No cookie banner found or failed to close it: %s", str(e))
            pass
