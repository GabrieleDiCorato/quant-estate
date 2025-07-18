"""
Quant Estate - Real estate data collection and analysis toolkit
"""

__version__ = "0.1.0"

from sources.config import ConfigManager
from sources.logging import setup_logging, get_logger
from sources.datamodel import ListingDetails, ListingId
from sources.exceptions import (
    ConnectorError,
    ScrapingError,
    StorageError,
    ValidationError,
    ConfigurationError
)
from sources.scrapers import SeleniumScraper
from sources.storage import Storage


from .config import ConfigManager
from .logging import setup_logging, get_logger
from .datamodel import ListingDetails
from .exceptions import (
    ConnectorError,
    ScrapingError,
    StorageError,
    ValidationError,
    ConfigurationError
)

__all__ = [
    'ConfigManager',
    'setup_logging',
    'get_logger',
    'ListingDetails',
    'ConnectorError',
    'ScrapingError',
    'StorageError',
    'ValidationError',
    'ConfigurationError',
    'SeleniumScraper',
    'Storage',
    'ListingId',
    '__version__'
]