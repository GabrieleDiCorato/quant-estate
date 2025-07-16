import csv

from pathlib import Path
from datetime import datetime
from typing import TypeVar, Type, Any
from collections.abc import Sequence, Mapping

from sources.connectors.storage.abstract_storage import AbstractStorage
from sources.exceptions import StorageError
from sources.logging.logging_mixin import LoggingMixin
from sources.datamodel.base_datamodel import QuantEstateDataObject

T = TypeVar("T", bound=QuantEstateDataObject)

class FileStorage[T](AbstractStorage[T], LoggingMixin):
    """File-based storage implementation using JSON and CSV files."""

    def __init__(self, config: ConfigManager, model_class: Type[T]):
        """
        Initialize file storage for a specific data model type.

        Args:
            base_path: Directory where files will be stored.
            model_class: The Pydantic model class (e.g., ListingDetails) that will be stored.
                         This is used to generate headers and filenames.
        """
        super().__init__()
        self.logger.info("Initializing FileStorage at %s for model %s", base_path, model_class.__name__)

        # Create session timestamp for file naming
        self.base_path = Path(base_path)
        self.model_class = model_class
        self.model_name = model_class.__name__.lower()
        self.fieldnames = list(model_class.model_fields.keys())

        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = self.base_path / f"real_estate_{self.session_timestamp}.csv"

        # Create directory if it doesn't exist
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.logger.error(
                "Failed to create storage directory at %s: %s",
                self.base_path,
                e,
                exc_info=True,
            )
            raise StorageError(f"Could not create storage directory: {e}") from e

        # Initialize CSV file with headers if it doesn't exist
        self._initialize_csv()

        self.logger.info("Initialized FileStorage at %s", self.base_path)

    def _initialize_csv(self):
        """Writes the header to the CSV file if it's new."""
        try:
            if not self.csv_path.exists():
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                    writer.writeheader()
        except IOError as e:
            self.logger.error("Failed to initialize CSV file at %s: %s", self.csv_path, e, exc_info=True)
            raise StorageError(f"Could not initialize CSV file: {e}") from e
        
    def append_data(self, data: Sequence[T]) -> bool:
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

        self.logger.info("Appending [%s] real estate listings", len(data))

        # Store as CSV
        self.logger.debug("Writing into CSV file: %s", self.csv_path)
        try:
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writerows([item.model_dump() for item in data])
            self.logger.info("Successfully appended %d records to CSV file", len(data))
            return True
        except Exception as e:
            self.logger.error("Failed to append to CSV: %s", str(e), exc_info=True)
            raise StorageError(f"Failed to append to CSV: {e}")
