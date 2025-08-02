import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
import re
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from sources.config.model.storage_settings import CsvStorageSettings
from sources.datamodel.enumerations import Source, EnergyClass
from sources.datamodel.listing_id import ListingId
from sources.datamodel.listing_details import ListingDetails
from sources.logging import logging_utils
from sources.scrapers.selenium_scraper import SeleniumScraper
from sources.storage.abstract_storage import Storage
from sources.storage.file_storage import FileStorage

BASE_URL = "https://www.immobiliare.it/"
URL_PREFIX = "https://www.immobiliare.it/annunci/"

class ImmobiliareListingScraper(SeleniumScraper):
    """Scraper for Immobiliare.it using Selenium. Given the URL for a specific listing, it extracts all relevant details."""

    def __init__(
        self,
        storage: Storage,
        listing_id: ListingId,
        base_url: str = BASE_URL,
        **kwargs,
    ):
        """Initialize the Immobiliare scraper with specific settings."""
        super().__init__(storage, base_url, scrape_url=listing_id.url, **kwargs)
        if not self.scrape_url.startswith(URL_PREFIX):
            raise ValueError(f"scrape_url must start with [{URL_PREFIX}], got [{self.scrape_url}]")

        self.listing_id = listing_id

        # Create instance-specific logger
        self.logger = logging.getLogger(f"{__name__}.{self._instance_id}")

    def scrape(self):
        """Main scraping method to collect property IDs."""

        # Automatically closes driver after use
        with self.get_driver() as driver:
            # self.warmup_driver(driver)

            # Navigate to the page
            self.logger.info("Navigating to scrape URL: %s", self.scrape_url)
            self.get_page(driver, self.scrape_url, wait_for_element=("CSS_SELECTOR", "h1.styles_ld-title__title__Ww2Gb"))

            # Close cookies banner if present (already present in warmup_driver)
            self._close_cookies(driver)
            self._realistic_wait()

            # Close login popup if present
            self._close_login_popup(driver)
            self._realistic_wait()

            # Random scroll before scraping
            driver.execute_script(f"window.scrollTo(0, {random.randint(100, 700)});")

            # Extract main components
            price: str = self._get_price(driver)
            location_parts: list[str] = self._get_location(driver)

            # Extract last update date
            last_update_date: datetime | None = self._get_last_update_date(driver)

            # Extract feature badges
            feature_badges: list[str] = self._get_feature_badges(driver)

            # Extract energy class
            energy_class: str | None = self._get_energy_class(driver)

            # Extract maintenance fee
            maintenance_fee: str | None = self._get_maintenance_fee(driver)

            price_sqm: str | None = self._get_price_per_sqm(driver)

            # Extract luxury indicator
            luxury_indicator: bool | None = self._get_luxury_indicator(driver)

            # Extract description title and extended description
            description_title, extended_description = self._get_description(driver)

            # Open characteristics dialog
            dialog_element = self._open_characteristics_dialog(driver)
            if dialog_element is None:
                self.logger.error("Failed to open characteristics dialog, skipping characteristics extraction.")
                raise ValueError("Failed to open characteristics dialog, cannot extract property details.") 
            self.logger.info("Successfully opened characteristics dialog, ready for data extraction")

            # Extract characteristics from the dialog
            characteristics = self._extract_characteristics(dialog_element)

        # Build ListingDetails object
        listing_details = self._build_listing_details(
            listing_id=self.listing_id,
            price=price,
            location_parts=location_parts,
            last_update_date=last_update_date,
            feature_badges=feature_badges,
            price_sqm=price_sqm,
            luxury_indicator=luxury_indicator,
            energy_class=energy_class,
            maintenance_fee=maintenance_fee,
            description_title=description_title,
            extended_description=extended_description,
            characteristics=characteristics
        )

        self.logger.info("Successfully created ListingDetails object")
        self.storage.append_data([listing_details])
        self.logger.info("Completed!")

    def _get_element(self, driver, by: str, value: str):
        """Helper method to get an element by its locator."""
        try:
            return driver.find_element(by, value)
        except Exception as e:
            self.logger.error("Element not found: %s, %s", by, value)
            raise ValueError(f"Element not found: {by}, {value}") from e

    def _get_title(self, driver) -> str:
        title_elem = self._get_element(driver, By.CSS_SELECTOR, "h1.styles_ld-title__title__Ww2Gb")
        title = title_elem.text.strip()
        self.logger.debug("Extracted title: %s", title)
        return title

    def _get_price(self, driver) -> str:
        price_elem = self._get_element(driver, By.CSS_SELECTOR, "div.Price_price__mzj0D span")
        price = price_elem.text.strip()
        self.logger.debug("Extracted price: %s", price)
        return price

    def _get_location(self, driver) -> list[str]:
        location_spans = driver.find_elements(By.CSS_SELECTOR, "button.styles_ld-blockTitle__link__paCwh span.styles_ld-blockTitle__location__n2mZJ")
        if not location_spans:
            self.logger.error("Location elements not found")
            raise ValueError("Location elements not found on the page")
        location_parts = [span.text.strip() for span in location_spans]
        self.logger.debug("Extracted location: %s", location_parts)
        return location_parts

    def _get_description(self, driver) -> tuple[str | None, str]:
        """Extract description title and extended description.
        
        Returns:
            tuple[str | None, str]: (title, extended_description) both normalized to single lines
        """
        try:
            # Scroll to the description section
            description_section = driver.find_element(By.CSS_SELECTOR, "div[data-tracking-key='description']")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", description_section)
            self._realistic_wait()

            # Extract the description title (optional)
            title = None
            try:
                title_elem = driver.find_element(By.CSS_SELECTOR, "p.styles_ld-descriptionHeading__title__ifRR2")
                title = self._normalize_text(title_elem.text)
                self.logger.debug("Extracted description title: %s", title)
            except Exception as title_e:
                self.logger.debug("Description title not found: %s", str(title_e).split('\n')[0])

            # Click the "leggi tutto" button to expand full description
            read_more_button = driver.find_element(By.CSS_SELECTOR, "button.styles_in-readAll__action___B8HW")
            driver.execute_script("arguments[0].click();", read_more_button)
            self._realistic_wait()

            # Extract the extended description after expansion
            description_container = driver.find_element(By.CSS_SELECTOR, "div.styles_in-readAll__04LDT div")
            extended_description = self._normalize_text(description_container.text)

            self.logger.debug("Extracted extended description length: %d chars", len(extended_description))

            return title, extended_description

        except Exception as e:
            self.logger.warning("Error extracting description: %s", str(e).split('\n')[0])
            self.logger.debug("Error extracting description", exc_info=True)
            return (None, "")

    def _get_last_update_date(self, driver) -> datetime | None:
        """Extract the last update date from the listing page.
        
        Returns:
            datetime: DateTime object with Rome timezone, or None if not found
        """

        try:
            # Find the last update element
            last_update_element = driver.find_element(By.CSS_SELECTOR, "div.styles_ld-lastUpdate__0G31u span.styles_ld-lastUpdate__text__KLqrs")
            last_update_text = last_update_element.text.strip()

            self.logger.debug("Found last update text: %s", last_update_text)

            # Extract date using regex pattern for dd/mm/yyyy format
            date_pattern = r'(\d{1,2})/(\d{1,2})/(\d{4})'
            match = re.search(date_pattern, last_update_text)

            if match:
                day, month, year = match.groups()
                # Convert to datetime object with Rome timezone
                rome_tz = ZoneInfo("Europe/Rome")
                datetime_obj = datetime(int(year), int(month), int(day), tzinfo=rome_tz)
                self.logger.info("Parsed last update date: %s -> %s", match.group(0), datetime_obj)
                return datetime_obj
            else:
                self.logger.warning("No date pattern found in text: %s", last_update_text)
                return None

        except Exception as e:
            self.logger.warning("Error extracting last update date: %s", str(e).split('\n')[0])
            self.logger.debug("Error extracting last update date", exc_info=True)
            return None

    def _get_feature_badges(self, driver) -> list[str]:
        """Extract feature badges from the listing page.
        
        Returns:
            list[str]: List of feature badge texts, empty list if none found
        """
        try:
            # Find the feature badges container
            badges_container = driver.find_element(By.CSS_SELECTOR, "div.styles_ld-featuresBadges__mJqLG ul.styles_ld-featuresBadges__list__MGuKy")

            # Find all badge elements
            badge_elements = badges_container.find_elements(By.CSS_SELECTOR, "li.styles_ld-featuresBadges__badge___8QgZ span.nd-badge")

            # Extract text from each badge
            badges = []
            for badge_element in badge_elements:
                badge_text = self._normalize_text(badge_element.text)
                if badge_text:  # Only add non-empty badges
                    badges.append(badge_text)

            self.logger.info("Found %d feature badges: %s", len(badges), badges)
            return badges

        except Exception as e:
            self.logger.warning("Error extracting feature badges: %s", str(e).split('\n')[0])
            self.logger.debug("Error extracting feature badges", exc_info=True)
            return []

    def _get_energy_class(self, driver) -> str | None:
        """Extract energy class from the listing page.
        
        Returns:
            str: Energy class letter (A, B, C, D, E, F, G, etc.), or None if not found
        """
        try:
            # Find the energy class element using the data-energy-class attribute
            energy_element = driver.find_element(By.CSS_SELECTOR, "span[data-energy-class]")

            # Get the energy class from the data attribute
            energy_class = energy_element.get_attribute("data-energy-class")

            if energy_class:
                energy_class = energy_class.strip().upper()
                self.logger.info("Found energy class: %s", energy_class)
                return energy_class
            else:
                self.logger.warning("Energy class data attribute is empty")
                return None

        except Exception as e:
            self.logger.warning("Error extracting energy class: %s", str(e).split('\n')[0])
            self.logger.debug("Error extracting energy class", exc_info=True)
            return None

    def _get_maintenance_fee(self, driver) -> str | None:
        """Extract monthly maintenance fee from the listing page.
        
        Returns:
            str: Maintenance fee text (e.g., "€ 70/mese"), or None if not found
        """
        try:
            # Find the costs section
            costs_section = driver.find_element(By.CSS_SELECTOR, "div[data-tracking-key='costs']")

            # Look for "Spese condominio" entry
            maintenance_elements = costs_section.find_elements(By.XPATH, ".//dt[contains(text(), 'Spese condominio')]/following-sibling::dd")

            if maintenance_elements:
                maintenance_fee = self._normalize_text(maintenance_elements[0].text)
                if maintenance_fee:
                    self.logger.info("Found maintenance fee: %s", maintenance_fee)
                    return maintenance_fee

            self.logger.warning("Maintenance fee not found in costs section")
            return None

        except Exception as e:
            self.logger.warning("Error extracting maintenance fee: %s", str(e).split('\n')[0])
            self.logger.debug("Error extracting maintenance fee", exc_info=True)
            return None

    def _get_price_per_sqm(self, driver) -> str | None:
        """Extract price per square meter from the listing page.
        
        Returns:
            str: Price per m² text (e.g., "3.558 €/m²"), or None if not found
        """
        try:
            # Find the price information section
            price_section = driver.find_element(By.CSS_SELECTOR, "div[data-tracking-key='price-information']")

            # Look for "Prezzo al m²" entry using XPath
            price_per_sqm_elements = price_section.find_elements(
                By.XPATH, 
                ".//dt[contains(text(), 'Prezzo al m²')]/following-sibling::dd"
            )

            if price_per_sqm_elements:
                price_per_sqm = self._normalize_text(price_per_sqm_elements[0].text)
                if price_per_sqm:
                    self.logger.info("Found price per m²: %s", price_per_sqm)
                    return price_per_sqm

            self.logger.warning("Price per m² not found in price information section")
            return None

        except Exception as e:
            self.logger.warning("Error extracting price per m²: %s", str(e).split('\n')[0])
            self.logger.debug("Error extracting price per m²", exc_info=True)
            return None

    def _get_luxury_indicator(self, driver) -> bool | None:
        """Extract luxury indicator from the main features section.
        
        Returns:
            bool: True if luxury indicator is present, None otherwise
        """
        try:
            # Look for the luxury indicator with diamond icon and "Lusso" text
            luxury_elements = driver.find_elements(By.XPATH, 
                "//div[contains(@class, 'styles_ld-mainFeatures__item')]//svg//use[@href='#diamond']/ancestor::div//span[contains(text(), 'Lusso')]"
            )

            if luxury_elements:
                self.logger.info("Found luxury indicator")
                return True
            else:
                self.logger.info("No luxury indicator found")
                return None

        except Exception as e:
            self.logger.warning("Error extracting luxury indicator: %s", str(e).split('\n')[0])
            self.logger.debug("Error extracting luxury indicator", exc_info=True)
            return None

    def _normalize_text(self, text: str) -> str:
        """Normalize text to a single line by handling whitespace and special characters.
        
        Args:
            text: Raw text to normalize
            
        Returns:
            str: Normalized single-line text
        """
        if not text:
            return ""

        # Strip leading/trailing whitespace
        normalized = text.strip()
        # Replace multiple consecutive whitespace characters (including newlines, tabs, spaces) with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        # Remove any remaining control characters except basic ones
        normalized = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', normalized)
        # Replace commas and semicolons to prevent CSV parsing issues
        normalized = re.sub(r"[,;]", ".", normalized)
        return normalized

    def _open_characteristics_dialog(self, driver) -> WebElement | None:
        """Navigate to and click the 'Vedi tutte le caratteristiche' button, then wait for dialog.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            WebElement: The dialog container element if found, None if failed
        """
        try:
            self.logger.info("Looking for 'Vedi tutte le caratteristiche' button")
            # Find the characteristics button
            characteristics_button = driver.find_element(By.CSS_SELECTOR, "button.styles_ld-primaryFeatures__openDialogButton___8v4x")

            # Scroll to the button to ensure it's visible
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", characteristics_button)
            self._realistic_wait()
            self.logger.info("Found 'Vedi tutte le caratteristiche' button, clicking it")

            # Wait for the button to be clickable
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.styles_ld-primaryFeatures__openDialogButton___8v4x"))
            )

            # Click the button using JavaScript for reliability
            driver.execute_script("arguments[0].click();", characteristics_button)
            self.logger.info("Successfully clicked 'Vedi tutte le caratteristiche' button")

            # Wait for the dialog to appear and return it
            self.logger.info("Waiting for characteristics dialog to appear...")
            dialog_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.nd-dialogFrame__container"))
            )
            self.logger.info("Successfully found characteristics dialog")

            # Small wait to ensure dialog is fully loaded
            self._realistic_wait()

            return dialog_element

        except Exception as e:
            self.logger.warning("Error opening characteristics dialog: %s", str(e).split('\n')[0])
            self.logger.debug("Error opening characteristics dialog", exc_info=True)
            return None

    def _extract_characteristics(self, dialog_element: WebElement) -> dict[str, str]:
        """Extract all key-value pairs from the characteristics dialog.
        
        Args:
            dialog_element: The dialog container WebElement
            
        Returns:
            dict[str, str]: Dictionary with characteristic names as keys and values as values
        """
        characteristics = {}

        try:
            # Find all feature containers within the dialog
            feature_elements = dialog_element.find_elements(By.CSS_SELECTOR, "div.styles_ld-primaryFeaturesDialogSection__feature__Maf3F")
            self.logger.debug("Found %d characteristic features in dialog", len(feature_elements))

            for feature in feature_elements:
                try:
                    # Extract the key (dt element)
                    key_element = feature.find_element(By.CSS_SELECTOR, "dt.styles_ld-primaryFeaturesDialogSection__featureTitle__VI7c0")
                    key = self._normalize_text(key_element.text)

                    # Extract the value (dd element)
                    value_element = feature.find_element(By.CSS_SELECTOR, "dd.styles_ld-primaryFeaturesDialogSection__featureDescription__G9ZGQ")
                    value = self._normalize_text(value_element.text)

                    if key and value:  # Only add non-empty pairs
                        characteristics[key] = value

                except Exception as feature_error:
                    self.logger.warning("Error extracting feature: %s", str(feature_error).split('\n')[0])
                    self.logger.debug("Error extracting feature", exc_info=True)
                    continue

            self.logger.info("Extracted characteristics: %s", characteristics)
            return characteristics

        except Exception as e:
            self.logger.error("Error extracting characteristics from dialog: %s", str(e))
            return characteristics

    def _build_listing_details(
        self,
        listing_id: ListingId,
        price: str,
        location_parts: list[str],
        last_update_date: datetime | None,
        feature_badges: list[str],
        energy_class: str | None,
        maintenance_fee: str | None,
        price_sqm: str | None,
        luxury_indicator: bool | None,
        description_title: str | None,
        extended_description: str,
        characteristics: dict[str, str]
    ) -> ListingDetails:
        """Build a ListingDetails object from extracted data using class builder pattern.
        
        Args:
            All extracted data from the scraping process
            
        Returns:
            ListingDetails: Validated ListingDetails object
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            # Validate required fields first
            self._validate_required_fields(
                price=price,
                location_parts=location_parts,
                description_title=description_title,
                extended_description=extended_description,
                characteristics=characteristics
            )

            # Parse location (format: [City, Quarter, Row])
            city = location_parts[0]
            country = "IT"
            address = "/".join(location_parts)

            # Parse price (e.g., "€ 300.000" -> 300000.0)
            price_eur = self._parse_price(price)

            # Parse price per square meter
            formatted_price_sqm, price_sqm_value = self._parse_price_per_sqm(price_sqm)

            # Parse maintenance fee (e.g., "€ 70/mese" -> 70.0)
            formatted_maintenance, maintenance = self._parse_maintenance_fee(maintenance_fee)

            # Parse surface (e.g., "35 m²" -> 35.0)
            surface_formatted = characteristics.get("Superficie")
            if not surface_formatted:
                raise ValueError("Surface information is required but not found in characteristics")
            surface = self._parse_surface(surface_formatted)

            # Extract property type and contract - required fields
            property_type = characteristics.get("Tipologia")
            if not property_type:
                raise ValueError("Property type (Tipologia) is required but not found in characteristics")

            contract = characteristics.get("Contratto")
            if not contract:
                raise ValueError("Contract type (Contratto) is required but not found in characteristics")

            # Build the ListingDetails object using class constructor
            return ListingDetails(
                # Core identifier
                id=listing_id.id,
                source=listing_id.source,
                title=listing_id.title,
                url=listing_id.url,
                last_updated=last_update_date,
                # Pricing - required fields
                formatted_price=price,
                price_eur=price_eur,
                formatted_maintenance_fee=formatted_maintenance,
                maintenance_fee=maintenance,
                formatted_price_sqm=formatted_price_sqm,
                price_sqm=price_sqm_value,
                # Property classification - required fields
                type=property_type,
                contract=contract,
                condition=characteristics.get("Stato"),
                is_luxury=luxury_indicator,
                # Property details - surface_formatted is required
                surface_formatted=surface_formatted,
                surface=surface,
                rooms=self._parse_int(characteristics.get("Locali")),
                floor=characteristics.get("Piano"),
                total_floors=self._parse_int(characteristics.get("Piani edificio")),
                # Composition
                bathrooms=self._parse_int(characteristics.get("Bagni")),
                bedrooms=self._parse_int(characteristics.get("Camere da letto")),
                balcony=self._parse_yes_no(characteristics.get("Balcone")),
                terrace=self._parse_yes_no(characteristics.get("Terrazzo")),
                elevator=self._parse_yes_no(characteristics.get("Ascensore")),
                garden=self._parse_garden(characteristics.get("Giardino")),
                cellar=self._parse_yes_no(characteristics.get("Cantina")),
                basement=None,  # Not directly available
                furnished=characteristics.get("Arredato"),
                kitchen=characteristics.get("Cucina"),
                # Building Info
                build_year=self._parse_int(characteristics.get("Anno di costruzione")),
                concierge=self._parse_concierge(characteristics.get("Servizio portineria")),
                is_accessible=self._parse_yes_no(characteristics.get("Accesso disabili")),
                # Energy and utilities
                heating_type=characteristics.get("Riscaldamento"),
                air_conditioning=characteristics.get("Climatizzazione"),
                energy_class=self._parse_energy_class(energy_class),
                # Location - required fields
                city=city,
                country=country,
                address=address,
                # Parking
                parking_info=characteristics.get("Box, posti auto"),
                # Extended description - required fields
                description_title=description_title,
                description=extended_description,
                other_amenities=feature_badges if feature_badges else None,
            )

        except Exception as e:
            self.logger.error("Error building ListingDetails: %s", str(e))
            raise ValueError(f"Failed to build ListingDetails: {e}") from e

    def _validate_required_fields(
        self,
        price: str,
        location_parts: list[str],
        description_title: str | None,
        extended_description: str,
        characteristics: dict[str, str]
    ) -> None:
        """Validate that all required fields are present and non-empty.
        
        Args:
            All required data for ListingDetails construction
            
        Raises:
            ValueError: If any required field is missing or empty
        """
        if not price or not price.strip():
            raise ValueError("Price is required but empty or None")

        if not location_parts or len(location_parts) == 0:
            raise ValueError("Location parts are required but empty or None")

        if not extended_description or not extended_description.strip():
            raise ValueError("Extended description is required but empty or None")

        if not characteristics:
            raise ValueError("Characteristics dictionary is required but empty or None")

        # Check for essential characteristics
        required_characteristics = ["Tipologia", "Contratto", "Superficie"]
        for req_char in required_characteristics:
            if req_char not in characteristics or not characteristics[req_char]:
                raise ValueError(f"Required characteristic '{req_char}' is missing or empty")

    def _parse_price(self, price_str: str) -> float:
        """Parse price string to float."""
        try:
            # Remove currency symbols and spaces, replace dots with nothing for thousands
            clean_price = re.sub(r'[€\s]', '', price_str)
            # Handle format like "300.000" -> 300000
            clean_price = clean_price.replace('.', '')
            return float(clean_price)
        except (ValueError, AttributeError):
            self.logger.warning("Could not parse price: %s", price_str)
            raise ValueError(f"Invalid price format: {price_str}") from None

    def _parse_maintenance_fee(self, fee_str: str | None) -> tuple[str | None, float | None]:
        """Parse maintenance fee string to float (monthly)."""
        if not fee_str:
            return None, None
        try:
            # Extract number from string like "€ 70/mese"
            numbers = re.findall(r'\d+', fee_str)
            if numbers:
                fee_str_lower = fee_str.lower()
                fee = float(numbers[0])
                # Check if it's already monthly
                if 'mese' in fee_str_lower or 'month' in fee_str_lower:
                    return fee_str, fee
                elif 'anno' in fee_str_lower or 'year' in fee_str_lower:
                    return fee_str, fee / 12  # Convert yearly to monthly
                else:
                    return fee_str, fee  # Assume monthly if no unit specified
        except (ValueError, AttributeError):
            self.logger.warning("Could not parse maintenance fee: %s", fee_str)
        return None, None

    def _parse_surface(self, surface_str: str) -> float | None:
        """Parse surface string to float."""
        if not surface_str:
            return None
        try:
            # Extract number from string like "35 m²"
            numbers = re.findall(r'\d+', surface_str)
            if numbers:
                return float(numbers[0])
        except (ValueError, AttributeError):
            self.logger.warning("Could not parse surface: %s", surface_str)
            raise ValueError(f"Invalid surface format: {surface_str}")

    def _parse_price_per_sqm(self, price_sqm_str: str | None) -> tuple[str | None, float | None]:
        """Parse price per square meter string to formatted string and float.

        Args:
            price_sqm_str: Price per m² string (e.g., "3.558 €/m²")

        Returns:
            tuple[str | None, float | None]: (formatted_price_sqm, price_sqm_value)
                - formatted_price_sqm: Simplified format (e.g., "3.558 EUR/sqm")
                - price_sqm_value: Numeric value as float
        """
        if not price_sqm_str:
            return None, None

        try:
            # Extract number from string like "3.558 €/m²" or "3.558,50 €/m²"
            number_match = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d+)?)', price_sqm_str)
            if number_match:
                number_str = number_match.group(1)
                # Convert European format to float: dot=thousands, comma=decimal
                clean_number = number_str.replace('.', '').replace(',', '.')
                price_value = float(clean_number)

                # Create simplified formatted string
                formatted_price = f"{number_str} EUR/sqm"

                self.logger.debug("Parsed price per m²: %s -> %s (%.2f)", price_sqm_str, formatted_price, price_value)
                return formatted_price, price_value
            else:
                self.logger.warning("Could not extract number from price per m²: %s", price_sqm_str)
                return None, None

        except (ValueError, AttributeError) as e:
            self.logger.warning("Could not parse price per m²: %s", str(e).split('\n')[0])
            self.logger.debug("Could not parse price per m²", exc_info=True)
            return None, None

    def _parse_energy_class(self, energy_class_str: str | None) -> EnergyClass | None:
        """Parse energy class string to EnergyClass enum."""
        if not energy_class_str:
            return None
        try:
            # Handle special cases like A+
            if energy_class_str == "A+":
                return EnergyClass.AP
            return EnergyClass(energy_class_str)
        except (ValueError, AttributeError):
            self.logger.warning("Could not parse energy class: %s", energy_class_str)
        return None

    def _parse_int(self, value_str: str | None) -> int | None:
        """Parse string to int."""
        if not value_str:
            return None
        try:
            # Extract first number from string
            numbers = re.findall(r'\d+', value_str)
            if numbers:
                return int(numbers[0])
        except (ValueError, AttributeError):
            pass
        return None

    def _parse_yes_no(self, value_str: str | None) -> bool | None:
        """Parse Yes/No string to boolean."""
        if not value_str:
            return None
        value_lower = value_str.lower()
        if 'sì' in value_lower or 'si' in value_lower or 'yes' in value_lower:
            return True
        elif 'no' in value_lower:
            return False
        return None

    def _parse_garden(self, garden_str: str | None) -> bool | None:
        """Parse garden string to boolean."""
        if not garden_str:
            return None
        if 'nessun' in garden_str.lower() or 'no' in garden_str.lower():
            return False
        return True

    def _parse_concierge(self, concierge_str: str | None) -> bool | None:
        """Parse concierge service string to boolean."""
        if not concierge_str:
            return None
        if 'portiere' in concierge_str.lower():
            return True
        return False

    def to_next_page(self, driver, current_page: int) -> bool:
        raise NotImplementedError("Pagination is not defined while scraping a specific listing")


# uv run --env-file sources/resources/config.dev.env sources/scrapers/immobiliare/scraper_listing.py
# See im_pipeline_listing.ipynb for a more interactive usage and extensive configuration using env variables and config files.
if __name__ == "__main__":  
    logging_utils.setup_logging(config_path="sources/resources/logging.yaml")

    storage: Storage = FileStorage(ListingId, CsvStorageSettings())
    test_listing_id = ListingId(
        source=Source.IMMOBILIARE, 
        source_id="122361988",
        title="Test Listing",
        url="https://www.immobiliare.it/annunci/122361988/"
    )
    scraper = ImmobiliareListingScraper(
        storage,
        scrape_url="https://www.immobiliare.it/annunci/122361988/",
        listing_id=test_listing_id
    )
    scraper.scrape()
