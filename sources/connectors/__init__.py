"""
Base classes and utilities for connectors.
"""

from .base import BaseConnector, BaseStorage, BaseScraper
from .exceptions import ScrapingError, StorageError, ValidationError, ConfigurationError

__all__ = [
    'BaseConnector',
    'BaseStorage',
    'BaseScraper',
    'ScrapingError',
    'StorageError',
    'ValidationError',
    'ConfigurationError'
]