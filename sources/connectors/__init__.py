"""
Base classes and utilities for connectors.
"""

from .base_scraper import AbstractScraper
from .base_storage import AbstractStorage
from .base_connector import AbstractConnector
from ..exceptions import ScrapingError, StorageError, ValidationError, ConfigurationError

__all__ = [
    'base_connector',
    'base_storage',
    'base_scraper',
    'ScrapingError',
    'StorageError',
    'ValidationError',
    'ConfigurationError'
]