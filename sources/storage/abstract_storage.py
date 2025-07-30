from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Type, TYPE_CHECKING

from sources.config.model.storage_settings import StorageSettings, StorageType
from sources.datamodel.base_datamodel import QuantEstateDataObject

if TYPE_CHECKING:
    from sources.storage.file_storage import FileStorage
    from sources.storage.mongo_storage import MongoDBStorage


class Storage[T: QuantEstateDataObject](ABC):
    """Abstract base class for data storage implementations."""

    @abstractmethod
    def append_data(self, data: Sequence[T]) -> bool:
        """Append data to storage.

        Args:
            data: List of data items to append

        Returns:
            bool: True if data was successfully appended

        Raises:
            StorageError: If there's an error storing the data
        """
        pass

    @classmethod
    def create_storage(cls, data_type: Type[T], config: StorageSettings) -> Storage[T]:
        """Factory method to create storage instance based on configuration.

        Args:
            data_type: The data type class
            config: StorageSettings instance with configuration

        Returns:
            Storage[T]: Instance of the appropriate storage implementation
        """
        # Import at runtime to avoid circular imports
        from sources.storage.file_storage import FileStorage
        from sources.storage.mongo_storage import MongoDBStorage

        if config.storage_type == StorageType.FILE:
            return FileStorage[T](data_type=data_type, config=config.file_settings)
        elif config.storage_type == StorageType.MONGODB:
            return MongoDBStorage[T](data_type=data_type, config=config.mongodb_settings)
        else:
            raise ValueError(f"Unsupported storage type: {config.storage_type}")
