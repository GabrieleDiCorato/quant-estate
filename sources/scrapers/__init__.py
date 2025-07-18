"""
Base classes and utilities for connectors.
"""

from .abstract_scraper import Scraper
from .storage.abstract_storage import Storage
from .connector import Connector
from ..exceptions import ScrapingError, StorageError, ValidationError, ConfigurationError

__all__ = [
    'connector',
    'abstract_scraper',
    'Storage',
    'ScrapingError',
    'StorageError',
    'ValidationError',
    'ConfigurationError'
]