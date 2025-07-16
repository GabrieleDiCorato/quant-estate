import csv
import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, TypeVar

from sources.connectors.storage.abstract_storage import AbstractStorage
from sources.datamodel.listing_details import ListingDetails
from sources.exceptions import StorageError
from sources.datamodel.base_datamodel import QuantEstateDataObject

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=QuantEstateDataObject)

class FileStorage[T](AbstractStorage[T]):
    """File-based storage implementation using JSON and CSV files."""

    def __init__(self, base_path: str):
        """Initialize file storage.

        Args:
            base_path: Directory where files will be stored
            save_json: Whether to save data in JSON format in addition to CSV
        """
        self.base_path = Path(base_path)

        # Create session timestamp for file naming
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = self.base_path / f"real_estate_{self.session_timestamp}.csv"

        # Create directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Initialize files with headers if they don't exist
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=ListingDetails.__annotations__.keys())
                writer.writeheader()

        logger.info("Initialized FileStorage at %s", self.base_path)

    def append_data(self, data: list[T]) -> bool:
        """Append data to storage.

        Args:
            data: List of RealEstate objects to append

        Returns:
            bool: True if data was successfully appended

        Raises:
            StorageError: If there's an error storing the data
        """
        if not data:
            logger.warning("No data to store")
            return False

        logger.info(f"Storing real estate listings", len(data))

        # Store as CSV
        logger.debug("Appending to CSV file: %s", self.csv_path)
        try:
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=ListingDetails.__annotations__.keys())
                writer.writerows([asdict(item) for item in data])
            logger.info("Successfully appended %d records to CSV file", len(data))
            return True
        except Exception as e:
            logger.error("Failed to append to CSV: %s", str(e), exc_info=True)
            raise StorageError(f"Failed to append to CSV: {e}")
