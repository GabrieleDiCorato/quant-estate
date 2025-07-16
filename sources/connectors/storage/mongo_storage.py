"""
Storage implementations for immobiliare.it data.
"""

from dataclasses import asdict
from typing import Iterable, TypeVar

from pymongo import MongoClient
from pymongo.write_concern import WriteConcern

from sources.connectors.storage.abstract_storage import AbstractStorage
from sources.logging.logging_mixin import LoggingMixin
from ...datamodel.base_datamodel import QuantEstateDataObject
from ...exceptions import StorageError

T = TypeVar("T", bound=QuantEstateDataObject)

class MongoDBStorage[T](AbstractStorage[T], LoggingMixin):
    """MongoDB-based storage implementation."""

    def __init__(self, connection_string: str, database: str, collection: str, **kwargs):
        """Initialize MongoDB storage.
        
        Args:
            connection_string: MongoDB connection string template
            database: Database name
            collection: Collection name
            **kwargs: Additional connection parameters (host, port, username, password, etc.)
        """
        self.config = {
            'connection_string': connection_string,
            'database': database,
            'collection': collection,
            **kwargs
        }
        self._client = None
        self._collection = None

        # Format the connection string with all parameters
        from urllib.parse import quote_plus
        formatted_connection = connection_string.format(
            username=quote_plus(self.config.get('username', '')),
            password=quote_plus(self.config.get('password', '')),
            host=self.config.get('host', 'localhost'),
            db_query=self.config.get('db_query', ''),
            database=database
        )
        self.config['connection_string'] = formatted_connection

        self.logger.info("Initialized MongoDBStorage [%s] for %s.%s", 
                        self.config['connection_string'], database, collection)

    def _get_collection(self):
        """Get MongoDB collection with proper write concern."""
        if self._collection is None:
            if self._client is None:
                self._client = MongoClient(self.config['connection_string'])
            db = self._client[self.config['database']]
            self._collection = db[self.config['collection']].with_options(
                write_concern=WriteConcern(w=1)
            )
        return self._collection

    def append_data(self, data: List[ListingDetails]) -> bool:
        """Append data to storage.
        
        Args:
            data: List of RealEstate objects to append
            
        Returns:
            bool: True if data was successfully appended
            
        Raises:
            StorageError: If there's an error storing the data
        """
        if not data:
            self.logger.warning("No data to store")
            return False

        self.logger.info("Storing %d real estate listings in MongoDB", len(data))
        try:
            collection = self._get_collection()

            # Convert RealEstate objects to dictionaries
            documents = [asdict(item) for item in data]

            # Insert documents with write concern
            result = collection.insert_many(documents)
            self.logger.info("Successfully inserted %d documents into MongoDB", len(result.inserted_ids))
            return True

        except Exception as e:
            self.logger.error("Failed to store data in MongoDB: %s", str(e), exc_info=True)
            raise StorageError(f"Failed to store data in MongoDB: {e}")

    def __del__(self):
        """Clean up MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self.logger.debug("Closed MongoDB connection")
