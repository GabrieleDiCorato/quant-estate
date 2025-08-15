"""
MongoDB storage implementation for QuantEstate domain objects.
"""

import logging
from collections.abc import Sequence
from contextlib import contextmanager

from pymongo import MongoClient
from pymongo.errors import BulkWriteError

from sources.config.model.storage_settings import MongoStorageSettings
from sources.datamodel.base_datamodel import QuantEstateDataObject
from sources.datamodel.listing_details import ListingDetails
from sources.datamodel.listing_id import ListingId
from sources.datamodel.listing_record import ListingRecord
from sources.exceptions import StorageError
from sources.storage.abstract_storage import Storage

logger = logging.getLogger(__name__)


class MongoDBStorage[T: QuantEstateDataObject](Storage[T]):
    """MongoDB-based storage implementation."""

    def __init__(self, data_type: type[T], config: MongoStorageSettings):
        """Initialize MongoDB storage.

        Args:
            data_type: The specific QuantEstateDataObject subclass to handle
            config: Configuration with MongoDB connection parameters
        """
        logger.info("Initializing MongoDBStorage for %s", data_type.__name__)
        logger.debug("MongoDB connection settings: %s", config)

        self.data_type = data_type
        self.config = config
        self.connection_string = self.config.connection_string
        self.database = self.config.database
        self.collection = self._get_collection_from_type(data_type)
        self._client = None

        # Test connection and log safely
        self._test_connection()
        self._ensure_indexes()

        logger.info("Initialized MongoDBStorage connection to [%s]", self.database)

    def _get_collection_from_type(self, data_type: type[T]) -> str:
        """Get MongoDB collection name based on data type."""
        if issubclass(data_type, ListingDetails):
            return self.config.collection_listings
        elif issubclass(data_type, ListingId):
            return self.config.collection_ids
        elif issubclass(data_type, ListingRecord):
            return self.config.collection_records
        else:
            raise ValueError(f"Unknown data type: {data_type}")

    def _test_connection(self) -> None:
        """Test MongoDB connection without exposing credentials."""
        try:
            with self._get_client() as client:
                client.admin.command('ping')
        except Exception as e:
            raise StorageError(f"Failed to connect to MongoDB: {e}") from e

    def _ensure_indexes(self) -> None:
        """Create necessary indexes for the collections."""
        try:
            with self._get_client() as client:
                db = client[self.database]

                # Create unique index on 'id' field for both collections
                # If the index already exists, it will be ignored
                ids_collection = db[self.config.collection_ids]
                ids_collection.create_index("id", unique=True)

                listings_collection = db[self.config.collection_listings]
                listings_collection.create_index("id", unique=True)

                records_collection = db[self.config.collection_records]
                records_collection.create_index("id", unique=True)

                logger.info("Ensured unique indexes on 'id' field")
        except Exception as e:
            logger.warning("Failed to create indexes: %s", str(e))

    @contextmanager
    def _get_client(self):
        """Context manager for MongoDB client with proper resource cleanup."""
        client = MongoClient(self.config.connection_string.get_secret_value())
        try:
            yield client
        finally:
            client.close()

    def append_data(self, data: Sequence[T]) -> int:
        """Append data to storage.

        Args:
            data: List of data objects to append

        Returns:
            int: The number of records successfully appended

        Raises:
            StorageError: If there's an error storing the data
        """
        if not data:
            logger.warning("No data to store")
            return 0

        logger.info("Storing %d %s records", len(data), self.data_type.__name__)

        try:
            with self._get_client() as client:
                db = client[self.database]
                db_collection = db[self.collection]
                # Exclude None values from serialization to avoid storing null fields in MongoDB
                documents = [item.model_dump(exclude_none=True) for item in data]

                # Use insert_many with ordered=False to continue on duplicates
                try:
                    result = db_collection.insert_many(documents, ordered=False)
                    inserted_count = len(result.inserted_ids)
                    logger.info(
                        "Successfully inserted %d new documents into collection: [%s]",
                        inserted_count,
                        self.collection,
                    )
                    return inserted_count
                except BulkWriteError as e:
                    # Extract successful insertions from bulk write exception
                    inserted_count = getattr(e, 'details', {}).get('nInserted', 0)
                    duplicate_count = len(documents) - inserted_count
                    logger.info(
                        "Inserted %d new documents, skipped %d duplicates in collection: [%s]",
                        inserted_count,
                        duplicate_count,
                        self.collection,
                    )
                    return inserted_count

        except Exception as e:
            logger.error("Failed to append to MongoDB: %s", str(e), exc_info=True)
            raise StorageError(f"Failed to append to MongoDB: {e}") from e

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self._client:
            self._client.close()
            self._client = None
