"""
Storage implementations for immobiliare.it data.
"""

import logging
from typing import Type, TypeVar
from urllib.parse import quote_plus
from collections.abc import Sequence
from contextlib import contextmanager

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from sources.connectors.storage.abstract_storage import Storage
from ...datamodel.base_datamodel import QuantEstateDataObject
from ...exceptions import StorageError


T = TypeVar("T", bound=QuantEstateDataObject)
logger = logging.getLogger(__name__)

class MongoDBStorage(Storage[T]):
    """MongoDB-based storage implementation."""

    def __init__(self, data_type: Type[T], config: dict):
        """Initialize MongoDB storage.
        
        Args:
            data_type: The specific QuantEstateDataObject subclass to handle
            config: Configuration dictionary with MongoDB connection parameters
        """
        self.data_type = data_type
        self.config = config

        # Format the connection string with all parameters
        connection_string = self.config.get('connection_string', 'mongodb://{username}:{password}@{host}/{db_query}')
        self.database = self.config.get('database', 'quant_estate')

        self.formatted_connection = connection_string.format(
            username=quote_plus(self.config.get('username', '')),
            password=quote_plus(self.config.get('password', '')),
            host=self.config.get('host', 'localhost'),
            db_query=self.config.get('db_query', ''),
            database=self.database
        )

        # Follow project naming convention: {source}_{data_type}
        type_name = data_type.__name__.lower()
        source_name = self.config.get('source', 'unknown')
        self.collection_name = self.config.get('collection', f"{source_name}_{type_name}")

        self._client = None
        
        # Test connection and log safely
        self._test_connection()
        logger.info("Initialized MongoDBStorage for %s.%s", self.database, self.collection_name)

    def _test_connection(self) -> None:
        """Test MongoDB connection without exposing credentials."""
        try:
            with self._get_client() as client:
                client.admin.command('ping')
        except Exception as e:
            raise StorageError(f"Failed to connect to MongoDB: {e}")

    @contextmanager
    def _get_client(self):
        """Context manager for MongoDB client with proper resource cleanup."""
        client = MongoClient(self.formatted_connection)
        try:
            yield client
        finally:
            client.close()

    def append_data(self, data: Sequence[T]) -> bool:
        """Append data to storage.

        Args:
            data: List of data objects to append

        Returns:
            bool: True if data was successfully appended

        Raises:
            StorageError: If there's an error storing the data
        """
        if not data:
            logger.warning("No data to store")
            return False

        logger.info("Storing %d %s records", len(data), self.data_type.__name__)

        try:
            with self._get_client() as client:
                db = client[self.database]
                collection = db[self.collection_name]
                
                # Convert each object to a dictionary and insert
                documents = [item.model_dump() for item in data]
                result = collection.insert_many(documents, ordered=False)
                
                logger.info("Successfully inserted %d documents into %s", 
                           len(result.inserted_ids), self.collection_name)
                return True
                
        except DuplicateKeyError as e:
            logger.warning("Duplicate key error during insertion: %s", str(e))
            return False
        except Exception as e:
            logger.error("Failed to append to MongoDB: %s", str(e), exc_info=True)
            raise StorageError(f"Failed to append to MongoDB: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self._client:
            self._client.close()
            self._client = None
