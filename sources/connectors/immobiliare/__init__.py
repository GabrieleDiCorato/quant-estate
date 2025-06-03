"""
Immobiliare.it web scraper package
"""

from .scraper import ImmobiliareScraper
from .connector import ImmobiliareConnector
from .storage import FileStorage, MongoDBStorage, DataStorage
from .models import RealEstate
from ..exceptions import (
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
    'RealEstate',
    'ScrapingError',
    'StorageError',
    'ValidationError',
    'ConfigurationError',
    '__version__'
]