"""
Immobiliare.it web scraper package
"""

from ..storage.file_storage import FileStorage
from ..storage.abstract_storage import AbstractStorage
from .scraper import ImmobiliareScraper
from .connector import ImmobiliareConnector
from ..storage.mongo_storage import MongoDBStorage
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
    'AbstractStorage',
    'ListingDetails',
    'ScrapingError',
    'StorageError',
    'ValidationError',
    'ConfigurationError',
    '__version__'
]