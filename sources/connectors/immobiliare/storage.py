"""
Storage implementations for immobiliare.it data.
"""

from abc import ABC, abstractmethod
import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

from .models import RealEstate
from .exceptions import StorageError
from ...utils.logging import get_logger

# Set up logging
logger = get_logger("quant_estate.storage.immobiliare")

class DataStorage(ABC):
    """Abstract base class for data storage implementations."""
    
    @abstractmethod
    def append_data(self, data: List[Dict[str, Any]]) -> bool:
        """Append data to storage."""
        pass
    
    @abstractmethod
    def load_data(self) -> List[RealEstate]:
        """Load all real estate data from storage."""
        pass

class FileStorage(DataStorage):
    """File-based storage implementation using JSON and CSV files."""
    
    def __init__(self, base_path: str, save_json: bool):
        """Initialize file storage."""
        self.base_path = Path(base_path)
        self.save_json = save_json
        self.logger = get_logger("quant_estate.storage.file")
        self.logger.info("Initialized FileStorage at %s (JSON saving: %s)", 
                        self.base_path, 
                        "enabled" if save_json else "disabled")
    
    def store(self, data: List[RealEstate]) -> bool:
        """Store data in JSON and CSV formats."""
        if not data:
            self.logger.warning("No data to store")
            return False
            
        self.logger.info("Storing %d real estate listings", len(data))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Store as JSON
        if self.save_json:
            json_path = self.base_path / f"real_estate_{timestamp}.json"
            self.logger.debug("Saving JSON to %s", json_path)
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump([item.dict() for item in data], f, ensure_ascii=False, indent=2)
                self.logger.info("Successfully saved %d records to JSON file", len(data))
            except Exception as e:
                self.logger.error("Failed to save JSON: %s", str(e), exc_info=True)
                return False
        
        # Store as CSV
        csv_path = self.base_path / f"real_estate_{timestamp}.csv"
        self.logger.debug("Saving CSV to %s", csv_path)
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=RealEstate.__fields__)
                writer.writeheader()
                writer.writerows([item.dict() for item in data])
            self.logger.info("Successfully saved %d records to CSV file", len(data))
            return True
        except Exception as e:
            self.logger.error("Failed to save CSV: %s", str(e), exc_info=True)
            return False
    
    def load_data(self) -> List[RealEstate]:
        """Load all real estate data from the CSV file."""
        try:
            with open(self.csv_file, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                data = [RealEstate.from_dict(row) for row in reader]
                self.logger.info("Successfully loaded %d records from CSV file", len(data))
                return data
        except IOError as e:
            self.logger.error("Failed to load CSV data: %s", str(e), exc_info=True)
            raise StorageError(f"Failed to load CSV data: {e}")

class MongoDBStorage(DataStorage):
    """MongoDB-based storage implementation."""
    
    def __init__(self, connection_string: str, database: str, collection: str):
        """Initialize MongoDB storage."""
        self.config = {
            'connection_string': connection_string,
            'database': database,
            'collection': collection
        }
        self.logger = get_logger("quant_estate.storage.mongodb")
        self.logger.info("Initialized MongoDBStorage for %s.%s", database, collection)
    
    def store(self, data: List[RealEstate]) -> bool:
        """Store data in MongoDB."""
        if not data:
            self.logger.warning("No data to store")
            return False
            
        self.logger.info("Storing %d real estate listings in MongoDB", len(data))
        try:
            client = MongoClient(self.config['connection_string'])
            db = client[self.config['database']]
            collection = db[self.config['collection']]
            
            # Convert RealEstate objects to dictionaries
            documents = [item.dict() for item in data]
            
            # Insert documents
            result = collection.insert_many(documents)
            self.logger.info("Successfully inserted %d documents into MongoDB", len(result.inserted_ids))
            return True
            
        except Exception as e:
            self.logger.error("Failed to store data in MongoDB: %s", str(e), exc_info=True)
            return False
        finally:
            if 'client' in locals():
                client.close()
                self.logger.debug("Closed MongoDB connection")