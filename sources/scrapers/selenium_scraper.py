"""
Abstract undetected Chrome scraper with human-like pacing and anti-detection features.
"""

import itertools
import logging
import random
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager

import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from sources.config.model.scraper_settings import ScraperSettings
from sources.storage.abstract_storage import Storage

from ..exceptions import ScrapingError

logger = logging.getLogger(__name__)


class SeleniumScraper(ABC):
    """Abstract base class for undetected Chrome-based web scrapers."""

    # Thread-safe atomic counter (to identify instances)
    _instance_counter = itertools.count(1)

    def __init__(self, storage: Storage, settings: ScraperSettings):
        """Initialize the scraper with configuration."""
        if not isinstance(settings, ScraperSettings):
            raise TypeError(f"Expected ScraperSettings, got {type(settings).__name__}")

        self.settings = settings
        self.storage = storage
        self.settings = settings

        # Get next instance number atomically
        self._instance_id = next(SeleniumScraper._instance_counter)

        # Create instance-specific logger
        self.logger = logging.getLogger(f"{__name__}.{self._instance_id}")
        self.logger.info("Initialized SeleniumScraper with headless: %s", self.settings.headless)

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

            # Disable images to save memory
            options.add_argument("--disable-images")
            # Alternative method using preferences
            prefs = {
                "profile.managed_default_content_settings.images": 2,  # Block images
                "profile.default_content_setting_values.notifications": 2,  # Block notifications
            }
            options.add_experimental_option("prefs", prefs)

            # Other optimizations
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-extensions")

            if self.settings.headless:
                options.add_argument("--headless=new")  # Use new headless mode
            else:
                options.add_argument("--start-maximized")

            # Create undetected Chrome driver
            driver = uc.Chrome(
                options=options,
                version_main=None,  # Auto-detect Chrome version
                driver_executable_path=None,  # Auto-download if needed
                browser_executable_path=None,  # Use system Chrome
            )

            # Configure timeouts
            driver.implicitly_wait(self.settings.implicit_wait)
            driver.set_page_load_timeout(self.settings.page_load_timeout)

            self.logger.info("Created undetected Chrome WebDriver instance")
            return driver

        except Exception as e:
            self.logger.error("Failed to create undetected Chrome WebDriver: %s", str(e), exc_info=True)
            raise ScrapingError(f"Failed to create WebDriver: {e}") from e

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
                self.logger.info("WebDriver session closed")
            except Exception as e:
                self.logger.warning("Error closing WebDriver: %s", str(e))

    def warmup_driver(self, driver, base_url: str):
        """Initialize browser session by visiting homepage and handling cookies."""
        # Visit the homepage to get cookies
        self.logger.info("Visiting homepage to initialize session...")
        self.get_page(driver, base_url)
        # Wait for cookies to load and close them
        self._close_cookies(driver)
        self._realistic_wait()
        self.logger.info("Session is warmed up!")

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
            self.logger.info("Navigating to: %s", url)
            driver.get(url)

            # Wait for specific element if provided
            if wait_for_element:
                by_str, locator = wait_for_element
                by = getattr(By, by_str.upper())
                WebDriverWait(driver, self.settings.implicit_wait).until(EC.presence_of_element_located((by, locator)))
                self.logger.debug("Successfully waited for element: %s", locator)

        except TimeoutException as e:
            self.logger.error("Timeout loading page %s: %s", url, str(e))
            raise ScrapingError(f"Timeout loading page: {e}") from e
        except WebDriverException as e:
            self.logger.error("WebDriver error loading page %s: %s", url, str(e))
            raise ScrapingError(f"WebDriver error: {e}") from e
        except Exception as e:
            self.logger.error("Unexpected error loading page %s: %s", url, str(e), exc_info=True)
            raise ScrapingError(f"Unexpected error loading page: {e}") from e

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

        self.logger.debug("Scrolled to bottom of page")

    def _realistic_wait(self) -> None:
        """Wait with realistic randomization to mimic human behavior."""
        # Generate base delay
        base_delay = random.uniform(self.settings.min_delay, self.settings.max_delay)
        jitter_delay = random.uniform(-0.2, 0.3)
        # Occasionally add longer pauses (5% chance) to simulate human distractions
        extra_pause = 0.0 if random.random() >= 0.05 else random.uniform(1.0, 3.0)
        delay = base_delay + jitter_delay + extra_pause

        self.logger.debug("Realistic wait: %.2f seconds", delay)
        time.sleep(delay)

    def _close_cookies(self, driver: uc.Chrome) -> None:
        """Close the cookies banner if present.

        Args:
            driver: WebDriver instance
        """
        # Try to dismiss any cookie banners or popups
        try:
            self.logger.info("Attempting to close cookies banner...")
            # Wait for the specific Didomi cookies button to be present and clickable
            accept_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
            accept_btn.click()
            self.logger.info("Successfully clicked cookies accept button")
        except TimeoutException:
            self.logger.warning("Cookies button not found within timeout")
        except Exception as e:
            self.logger.warning("Failed to close cookies banner: %s", str(e))

    def _close_login_popup(self, driver: uc.Chrome) -> None:
        """Close the login popup if it appears."""
        try:
            self.logger.info("Waiting to close login popup...")
            # Wait for the login popup to appear
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ab-in-app-message.ab-modal")))
            # Find and click the close button
            self.logger.info("Attempting to close login popup...")
            close_button = driver.find_element(By.CSS_SELECTOR, "button.ab-close-button")
            self._realistic_wait()  # Wait before clicking
            close_button.click()
            self.logger.info("Closed login popup")
        except TimeoutException:
            self.logger.warning("Login popup did not appear")
        except Exception as e:
            self.logger.warning("Error closing login popup: %s", str(e))
            # Click on a random safe location to dismiss any remaining overlays
            try:
                # Get page dimensions
                viewport_width = driver.execute_script("return window.innerWidth")
                viewport_height = driver.execute_script("return window.innerHeight")

                # Click on a safe area (center region, avoiding edges)
                safe_x = random.randint(int(viewport_width * 0.3), int(viewport_width * 0.7))
                safe_y = random.randint(int(viewport_height * 0.3), int(viewport_height * 0.7))

                driver.execute_script(f"document.elementFromPoint({safe_x}, {safe_y}).click();")
                self.logger.debug("Clicked on safe location (%d, %d) to dismiss overlays", safe_x, safe_y)
            except Exception as click_error:
                self.logger.error("Could not click on safe location: %s", str(click_error))

    @abstractmethod
    def to_next_page(self, driver, current_page: int) -> bool:
        """Abstract method to navigate to the next page."""
        pass
