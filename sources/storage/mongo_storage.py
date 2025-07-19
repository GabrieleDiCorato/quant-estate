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

from sources.config.model.storage_settings import MongoStorageSettings
from sources.storage.abstract_storage import Storage
from sources.datamodel.listing_details import ListingDetails
from sources.datamodel.base_datamodel import QuantEstateDataObject
from sources.exceptions import StorageError


T = TypeVar("T", bound=QuantEstateDataObject)
logger = logging.getLogger(__name__)

class MongoDBStorage(Storage[T]):
    """MongoDB-based storage implementation."""

    def __init__(self, data_type: Type[T], config: MongoStorageSettings):
        """Initialize MongoDB storage.
        
        Args:
            data_type: The specific QuantEstateDataObject subclass to handle
            config: Configuration with MongoDB connection parameters
        """
        logger.info("Initializing MongoDBStorage for %s", data_type.__name__)
        logger.debug("MongoDB connection settings: %s", config)

        self.data_type = data_type
        self.config = config

        # Format the connection string with all parameters
        self.connection_string = self.config.connection_string
        self.database = self.config.database

        self._client = None

        # Test connection and log safely
        self._test_connection()
        logger.info("Initialized MongoDBStorage connection to [%s]", self.database)

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
        client = MongoClient(self.config.connection_string.get_secret_value())
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
                collection_str = self.config.collection_listings if isinstance(data[0], ListingDetails) else self.config.collection_ids
                db_collection = db[collection_str]

                # Convert each object to a dictionary and insert
                documents = [item.model_dump() for item in data]
                result = db_collection.insert_many(documents, ordered=False)

                logger.info(
                    "Successfully inserted %d documents into collection: [%s]",
                    len(result.inserted_ids),
                    collection_str,
                )
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
