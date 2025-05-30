from abc import ABC, abstractmethod
import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from .models import RealEstate
from .exceptions import StorageError
from .config import config

class DataStorage(ABC):
    """Abstract base class for data storage implementations."""
    
    @abstractmethod
    def append_data(self, data: List[Dict[str, Any]]) -> bool:
        """Append data to storage.
        
        Args:
            data: List of real estate data dictionaries to append
            
        Returns:
            bool: True if append was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def load_data(self) -> List[RealEstate]:
        """Load all real estate data from storage."""
        pass

class FileStorage(DataStorage):
    """File-based storage implementation using JSON and CSV files."""
    
    def __init__(self, base_path: str = None):
        """Initialize the storage with an optional custom base path."""
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Get the absolute path to the project root
            project_root = Path(__file__).parent.parent.parent.parent
            # Get the base folder name from config and append current date
            folder_name = config.storage_settings.get("folder_name", "immobiliare_data")
            date_str = datetime.now().strftime(config.storage_settings.get("date_format", "%Y-%m-%d"))
            folder_name = f"{folder_name}_{date_str}"
            
            self.base_path = project_root / "data" / folder_name
        
        self._ensure_directory_exists()
        print(f"Initialized storage at: {self.base_path}")
        
        # Initialize file paths
        self.json_file = self.base_path / config.storage_settings.get("default_json_filename", "immobiliare.json")
        self.csv_file = self.base_path / config.storage_settings.get("default_csv_filename", "immobiliare.csv")
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the storage directory exists."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            print(f"Storage directory: {self.base_path}")
        except OSError as e:
            raise StorageError(f"Failed to create storage directory: {e}")
    
    def _initialize_files(self) -> None:
        """Initialize JSON and CSV files if they don't exist."""
        # Initialize JSON file
        if not self.json_file.exists():
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump([], f)
            print(f"Initialized JSON file: {self.json_file}")
        
        # Initialize CSV file
        if not self.csv_file.exists():
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                # We'll write the header when we have data
                pass
            print(f"Initialized CSV file: {self.csv_file}")
    
    def append_data(self, data: List[Dict[str, Any]]) -> bool:
        """Append data to both JSON and CSV files.
        
        Args:
            data: List of real estate data dictionaries to append
            
        Returns:
            bool: True if append was successful to either format, False otherwise
        """
        if not data:
            print("No data to append")
            return False
            
        json_success = self._append_json(data)
        csv_success = self._append_csv(data)
        
        return json_success or csv_success
    
    def _append_json(self, data: List[Dict[str, Any]]) -> bool:
        """Append data to the JSON file."""
        try:
            # Read existing data
            existing_data = []
            if self.json_file.exists() and self.json_file.stat().st_size > 0:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            
            # Append new data
            existing_data.extend(data)
            
            # Write back all data
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
            
            print(f"Appended {len(data)} records to JSON file: {self.json_file}")
            return True
            
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to append JSON data: {e}")
            return False
    
    def _append_csv(self, data: List[Dict[str, Any]]) -> bool:
        """Append data to the CSV file."""
        try:
            # Check if file exists and has content
            file_exists = self.csv_file.exists() and self.csv_file.stat().st_size > 0
            
            # Open file in append mode
            with open(self.csv_file, "a", newline="", encoding="utf-8") as csvfile:
                if data:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    # Write header only if file is new
                    if not file_exists:
                        writer.writeheader()
                    
                    # Write the data
                    writer.writerows(data)
            
            print(f"Appended {len(data)} records to CSV file: {self.csv_file}")
            return True
            
        except IOError as e:
            print(f"Warning: Failed to append CSV data: {e}")
            return False
    
    def load_data(self) -> List[RealEstate]:
        """Load all real estate data from the JSON file."""
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [RealEstate.from_dict(item) for item in data]
        except (IOError, json.JSONDecodeError) as e:
            raise StorageError(f"Failed to load JSON data: {e}")

class MongoDBStorage(DataStorage):
    """MongoDB-based storage implementation."""
    
    def __init__(self, connection_string: str, database: str = "immobiliare", collection: str = "properties"):
        """Initialize MongoDB storage.
        
        Args:
            connection_string: MongoDB connection string
            database: Database name
            collection: Collection name
        """
        try:
            from pymongo import MongoClient
            self.client = MongoClient(connection_string)
            self.db = self.client[database]
            self.collection = self.db[collection]
            print(f"Connected to MongoDB: {database}.{collection}")
        except ImportError:
            raise StorageError("pymongo package is required for MongoDB storage")
        except Exception as e:
            raise StorageError(f"Failed to connect to MongoDB: {e}")
    
    def append_data(self, data: List[Dict[str, Any]]) -> bool:
        """Insert data into MongoDB collection.
        
        Args:
            data: List of real estate data dictionaries to append
            
        Returns:
            bool: True if insert was successful, False otherwise
        """
        if not data:
            print("No data to append")
            return False
            
        try:
            result = self.collection.insert_many(data)
            print(f"Inserted {len(result.inserted_ids)} records into MongoDB")
            return True
        except Exception as e:
            print(f"Warning: Failed to insert data into MongoDB: {e}")
            return False
    
    def load_data(self) -> List[RealEstate]:
        """Load all real estate data from MongoDB."""
        try:
            cursor = self.collection.find({})
            return [RealEstate.from_dict(doc) for doc in cursor]
        except Exception as e:
            raise StorageError(f"Failed to load data from MongoDB: {e}")
    
    def __del__(self):
        """Close MongoDB connection when object is destroyed."""
        if hasattr(self, 'client'):
            self.client.close()