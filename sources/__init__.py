"""
Quant Estate - Real estate data collection and analysis toolkit
"""

__version__ = "0.1.0"

from .connectors.AbstractScraper import AbstractScraper
from .connectors.AbstractStorage import AbstractStorage
from .connectors.BaseConnector import AbstractConnector
from .config import ConfigManager
from .logging import setup_logging, get_logger
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
    'ConnectorError',
    'ScrapingError',
    'StorageError',
    'ValidationError',
    'ConfigurationError',
    '__version__'
]