"""
Quant Estate - Real estate data collection and analysis toolkit
"""

__version__ = "0.1.0"

from .connectors.base_scraper import AbstractScraper
from .connectors.base_storage import AbstractStorage
from .connectors.base_connector import AbstractConnector
from .config import ConfigManager
from .logging import setup_logging, get_logger
from .datamodel import RealEstateListing
from .exceptions import (
    ConnectorError,
    ScrapingError,
    StorageError,
    ValidationError,
    ConfigurationError
)

__all__ = [
    'AbstractConnector',
    'AbstractStorage',
    'AbstractScraper',
    'ConfigManager',
    'setup_logging',
    'get_logger',
    'RealEstateListing',
    'ConnectorError',
    'ScrapingError',
    'StorageError',
    'ValidationError',
    'ConfigurationError',
    '__version__'
]