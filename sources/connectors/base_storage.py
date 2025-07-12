from abc import ABC, abstractmethod
from typing import Any

class AbstractStorage(ABC):
    """Abstract base class for data storage implementations."""

    @abstractmethod
    def append_data(self, data: list[dict[str, Any]]) -> bool:
        """Append data to storage.

        Args:
            data: List of data items to append

        Returns:
            bool: True if data was successfully appended

        Raises:
            StorageError: If there's an error storing the data
        """
        pass

    @abstractmethod
    def load_data(self) -> list[Any]:
        """Load all data from storage.

        Returns:
            List of data items

        Raises:
            StorageError: If there's an error loading the data
        """
        pass