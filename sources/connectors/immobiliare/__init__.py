"""
Immobiliare.it web scraper package
"""

from .scraper import ImmobiliareScraper
from .connector import ImmobiliareConnector
from .storage import FileStorage, MongoDBStorage, DataStorage
from ...datamodel.real_estate_listing import RealEstateListing
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
    'RealEstateListing',
    'ScrapingError',
    'StorageError',
    'ValidationError',
    'ConfigurationError',
    '__version__'
]