"""
Storage implementations for immobiliare.it data.
"""

# Standard library imports
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List

# Third-party imports
import csv
import json
from pymongo import MongoClient
from pymongo.write_concern import WriteConcern

# Local imports
from .models import RealEstate
from ..exceptions import StorageError
from ...logging.logging import get_module_logger, get_class_logger

# Set up logging
logger = get_module_logger()

class DataStorage(ABC):
    """Abstract base class for data storage implementations."""
    
    @abstractmethod
    def append_data(self, data: List[RealEstate]) -> bool:
        """Append data to storage.
        
        Args:
            data: List of RealEstate objects to append
            
        Returns:
            bool: True if data was successfully appended
            
        Raises:
            StorageError: If there's an error storing the data
        """
        pass

class FileStorage(DataStorage):
    """File-based storage implementation using JSON and CSV files."""
    
    def __init__(self, base_path: str, save_json: bool = False):
        """Initialize file storage.
        
        Args:
            base_path: Directory where files will be stored
            save_json: Whether to save data in JSON format in addition to CSV
        """
        self.base_path = Path(base_path)
        self.save_json = save_json
        self.logger = get_class_logger(self.__class__)
        self.logger.info("Initialized FileStorage at %s (JSON saving: %s)", 
                        self.base_path, 
                        "enabled" if save_json else "disabled")
    
    def append_data(self, data: List[RealEstate]) -> bool:
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
            
        self.logger.info("Storing %d real estate listings", len(data))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Store as JSON if enabled
        if self.save_json:
            json_path = self.base_path / f"real_estate_{timestamp}.json"
            self.logger.debug("Saving JSON to %s", json_path)
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump([asdict(item) for item in data], f, ensure_ascii=False, indent=2)
                self.logger.info("Successfully saved %d records to JSON file", len(data))
            except Exception as e:
                self.logger.error("Failed to save JSON: %s", str(e), exc_info=True)
                raise StorageError(f"Failed to save JSON: {e}")
        
        # Store as CSV
        csv_path = self.base_path / f"real_estate_{timestamp}.csv"
        self.logger.debug("Saving CSV to %s", csv_path)
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=RealEstate.__annotations__.keys())
                writer.writeheader()
                writer.writerows([asdict(item) for item in data])
            self.logger.info("Successfully saved %d records to CSV file", len(data))
            return True
        except Exception as e:
            self.logger.error("Failed to save CSV: %s", str(e), exc_info=True)
            raise StorageError(f"Failed to save CSV: {e}")

class MongoDBStorage(DataStorage):
    """MongoDB-based storage implementation."""
    
    def __init__(self, connection_string: str, database: str, collection: str):
        """Initialize MongoDB storage."""
        self.config = {
            'connection_string': connection_string,
            'database': database,
            'collection': collection
        }
        self.logger = get_class_logger(self.__class__)
        self._client = None
        self._collection = None
        self.logger.info("Initialized MongoDBStorage for %s.%s", database, collection)
    
    def _get_collection(self):
        """Get MongoDB collection with proper write concern."""
        if self._collection is None:
            if self._client is None:
                self._client = MongoClient(self.config['connection_string'])
            db = self._client[self.config['database']]
            self._collection = db[self.config['collection']].with_options(
                write_concern=WriteConcern(w=1, journal=True)
            )
        return self._collection
    
    def append_data(self, data: List[RealEstate]) -> bool:
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