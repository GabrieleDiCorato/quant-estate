from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TypeVar

from sources.datamodel.base_datamodel import QuantEstateDataObject

T = TypeVar("T", bound=QuantEstateDataObject)

class Storage[T](ABC):
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
