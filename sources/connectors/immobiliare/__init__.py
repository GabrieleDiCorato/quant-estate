"""
Immobiliare.it web scraper package
"""

from .scraper import ImmobiliareScraper
from .connector import ImmobiliareConnector
from .storage import FileStorage, MongoDBStorage, DataStorage
from .models import RealEstate
from .exceptions import (
    ImmobiliareError,
    InvalidURLError,
    RequestError,
    DataExtractionError,
    StorageError
)

__version__ = "0.1.0"

__all__ = [
    'ImmobiliareScraper',
    'ImmobiliareConnector',
    'FileStorage',
    'MongoDBStorage',
    'DataStorage',
    'RealEstate',
    'ImmobiliareError',
    'InvalidURLError',
    'RequestError',
    'DataExtractionError',
    'StorageError'
]