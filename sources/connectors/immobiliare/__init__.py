"""
Immobiliare.it web scraper package
"""

from .scraper import ImmobiliareScraper
from .connector import ImmobiliareConnector
from .storage import FileStorage, MongoDBStorage, DataStorage
from ...datamodel.listing_details import ListingDetails
from ...exceptions import (
    ScrapingError,
    StorageError,
    ValidationError,
    ConfigurationError
)

__version__ = "0.1.0"

__all__ = [
    'ImmobiliareScraper',
    'ImmobiliareConnector',
    'FileStorage',
    'MongoDBStorage',
    'DataStorage',
    'ListingDetails',
    'ScrapingError',
    'StorageError',
    'ValidationError',
    'ConfigurationError',
    '__version__'
]