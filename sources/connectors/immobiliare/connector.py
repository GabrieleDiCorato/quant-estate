"""
Immobiliare.it connector implementation.
"""

from typing import List, Dict, Any, Optional

from ..base_connector import AbstractConnector
from ...exceptions import ScrapingError, StorageError, ValidationError, ConfigurationError
from ...config import ConfigManager
from ...datamodel.real_estate_listing import RealEstateListing
from .scraper import ImmobiliareScraper
from .storage import FileStorage, MongoDBStorage
from ...logging_utils.logging import get_module_logger, get_class_logger, setup_logging

class ImmobiliareConnector(AbstractConnector):
    """Connector implementation for immobiliare.it."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the connector with configuration."""
        try:
            # Set up project-wide logging
            setup_logging(config_manager.get_logging_config())
            self.logger = get_class_logger(self.__class__)
            self.logger.info("Initializing ImmobiliareConnector")

            # Initialize components
            scraper = ImmobiliareScraper(config_manager.get_connector_config('immobiliare'))
            storage = self._create_storage(config_manager.get_storage_config('immobiliare'))
            super().__init__(scraper, storage)
            logger.info("ImmobiliareConnector initialized successfully with %s storage", 
                       storage.__class__.__name__)
        except Exception as e:
            logger.error("Failed to initialize ImmobiliareConnector: %s", str(e), exc_info=True)
            raise ConfigurationError(f"Failed to initialize connector: {e}")

    def _create_storage(self, storage_config: Dict[str, Any]):
        """Create storage instance based on configuration."""
        logger.debug("Creating storage with config: %s", storage_config)
        try:
            storage_type = storage_config['type']
            settings = storage_config['settings']

            if storage_type == 'file':
                storage = FileStorage(
                    base_path=settings['base_path'],
                    save_json=settings['save_json']
                )
                logger.info("Created FileStorage at %s", storage.base_path)
                return storage
            elif storage_type == 'mongodb':
                storage = MongoDBStorage(
                    connection_string=settings['connection_string'],
                    database=settings['database'],
                    collection=settings['collection'],
                    username=settings.get('username', ''),
                    password=settings.get('password', ''),
                    host=settings.get('host', 'localhost'),
                    db_query=settings.get('db_query', '')
                )
                logger.info("Created MongoDBStorage for %s.%s", 
                           storage.config['database'], 
                           storage.config['collection'])
                return storage
            else:
                raise ConfigurationError(f"Unsupported storage type: {storage_type}")
        except KeyError as e:
            raise ConfigurationError(f"Missing required storage configuration key: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to create storage: {e}")

    def scrape_and_store(self, start_url: str, max_pages: int = None) -> bool:
        """Scrape data from the given URL and store it."""
        logger.info("Starting scraping from %s (max pages: %s)", 
                   start_url, 
                   str(max_pages) if max_pages else "unlimited")
        try:
            result = super().scrape_and_store(start_url, max_pages)
            logger.info("Scraping completed successfully")
            return result
        except (ScrapingError, StorageError, ValidationError) as e:
            logger.error("Error during scraping: %s", str(e), exc_info=True)
            raise
        except Exception as e:
            logger.error("Unexpected error during scraping: %s", str(e), exc_info=True)
            raise ScrapingError(f"Unexpected error: {e}") 
