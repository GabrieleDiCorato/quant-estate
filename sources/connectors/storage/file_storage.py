from collections.abc import Sequence
import csv
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Type, TypeVar

from sources.config.model.storage_settings import CsvStorageSettings
from sources.connectors.storage.abstract_storage import Storage
from sources.exceptions import StorageError
from sources.datamodel.base_datamodel import QuantEstateDataObject


T = TypeVar("T", bound=QuantEstateDataObject)
logger = logging.getLogger(__name__)

class FileStorage(Storage[T]):
    """File-based storage implementation using CSV files."""

    def __init__(self, data_type: Type[T], config: CsvStorageSettings):
        """Initialize file storage.

        Args:
            base_path: Directory where files will be stored
            data_type: The specific QuantEstateDataObject subclass to handle
        """
        self.base_path = config.base_path
        self.data_type = data_type

        # Create session timestamp for file naming
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        type_name = data_type.__name__.lower()
        self.csv_path = self.base_path / f"{type_name}_{self.session_timestamp}.csv"

        # Create directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Initialize CSV file with headers if it doesn't exist
        if not self.csv_path.exists():
            self._initialize_csv()

        logger.info("Initialized FileStorage for %s at %s", data_type.__name__, self.base_path)

    def _initialize_csv(self) -> None:
        """Initialize CSV file with appropriate headers for the data type."""
        field_names = list(self.data_type.model_fields.keys())

        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=field_names)
            writer.writeheader()

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

        logger.info("Storing [%d] records of type [%s]", len(data), self.data_type.__name__)

        try:
            field_names = list(self.data_type.model_fields.keys())

            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=field_names)
                writer.writerows([item.model_dump() for item in data])

            logger.info("Successfully appended %d records to CSV file", len(data))
            return True
        except Exception as e:
            logger.error("Failed to append to CSV: %s", str(e), exc_info=True)
            raise StorageError(f"Failed to append to CSV: {e}")

    def _load_data(self) -> Sequence[T]:
        """Load all data from storage.

        Returns:
            List of data objects

        Raises:
            StorageError: If there's an error loading the data
        """
        if not self.csv_path.exists():
            logger.warning("CSV file does not exist: %s", self.csv_path)
            return []

        logger.info("Loading data from CSV file: %s", self.csv_path)
        try:
            with open(self.csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                data = [self.data_type(**row) for row in reader]

            logger.info("Successfully loaded %d records from CSV file", len(data))
            return data
        except Exception as e:
            logger.error("Failed to load data from CSV: %s", str(e), exc_info=True)
            raise StorageError(f"Failed to load data from CSV: {e}")
