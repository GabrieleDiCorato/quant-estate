"""
Base classes and utilities for connectors.
"""

from .AbstractScraper import AbstractScraper
from .AbstractStorage import AbstractStorage
from .BaseConnector import AbstractConnector
from ..exceptions import ScrapingError, StorageError, ValidationError, ConfigurationError

__all__ = [
    'AbstractConnector',
    'AbstractStorage',
    'AbstractScraper',
    'ScrapingError',
    'StorageError',
    'ValidationError',
    'ConfigurationError'
]