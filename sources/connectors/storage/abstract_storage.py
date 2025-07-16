from sources.datamodel.base_datamodel import QuantEstateDataObject

from abc import ABC, abstractmethod
from typing import TypeVar
from collections.abc import Sequence

T = TypeVar("T", bound=QuantEstateDataObject)

class AbstractStorage[T](ABC):
    """Abstract base class for data storage implementations."""

    @abstractmethod
    def append_data(self, data: Sequence[T]) -> bool:
        """Append data to storage.

        Args:
            data: List of RealEstate objects to append

        Returns:
            bool: True if data was successfully appended

        Raises:
            StorageError: If there's an error storing the data
        """
        pass
