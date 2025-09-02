"""
Quant Estate - Real estate data collection and analysis toolkit
"""

__version__ = "1.0.0"

from .config import ConfigManager
from .config.model import CsvStorageSettings, MongoStorageSettings, StorageSettings, StorageType
from .datamodel import ContractType, ListingDetails, ListingId, QuantEstateDataObject
from .exceptions import (
    ConfigurationError,
    ConnectorError,
    ScrapingError,
    StorageError,
    ValidationError,
)
from .logging import get_logger, setup_logging
from .scrapers import ImmobiliareIdScraper, ImmobiliareListingScraper, SeleniumScraper
from .storage import FileStorage, MongoDBStorage, Storage

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
