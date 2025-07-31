"""
Quant Estate - Real estate data collection and analysis toolkit
"""

__version__ = "0.1.0"

from .config import ConfigManager
from .config.model import CsvStorageSettings, MongoStorageSettings, StorageSettings, StorageType
from .logging import setup_logging, get_logger
from .datamodel import ListingDetails, ListingId, QuantEstateDataObject, ContractType
from .exceptions import (
    ConnectorError,
    ScrapingError,
    StorageError,
    ValidationError,
    ConfigurationError
)
from .storage import Storage, FileStorage, MongoDBStorage
from .scrapers import SeleniumScraper, ImmobiliareIdScraper, ImmobiliareListingScraper

__all__ = [
    "ConfigManager",
    "setup_logging",
    "get_logger",
    "ListingDetails",
    "ListingId",
    "QuantEstateDataObject",
    "ContractType",
    "ConnectorError",
    "ScrapingError",
    "StorageError",
    "ValidationError",
    "ConfigurationError",
    "Storage",
    "FileStorage",
    "MongoDBStorage",
    "CsvStorageSettings",
    "MongoStorageSettings",
    "StorageSettings",
    "StorageType",
    "SeleniumScraper",
    "ImmobiliareIdScraper",
    "ImmobiliareListingScraper",
    "__version__",
]
