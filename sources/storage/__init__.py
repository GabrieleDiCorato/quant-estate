"""
Storage implementations for the quant-estate project.

This package provides abstract base classes and concrete implementations
for storing real estate data in various formats and destinations.
"""

from .abstract_storage import Storage
from .file_storage import FileStorage
from .mongo_storage import MongoDBStorage

__all__ = [
    "Storage",
    "FileStorage",
    "MongoDBStorage",
]
