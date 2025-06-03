"""
Storage implementations for real estate data.
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
    
    def __init__(self, base_path: str = None, save_json: bool = False):
        """Initialize the storage with an optional custom base path."""
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Get the absolute path to the project root
            project_root = Path(__file__).parent.parent.parent.parent
            # Create data directory with current date
            date_str = datetime.now().strftime("%Y-%m-%d")
            self.base_path = project_root / "data" / f"immobiliare_data_{date_str}"
        
        self.save_json = save_json
        self._ensure_directory_exists()
        print(f"Storage initialized at: {self.base_path}")
        
        # Initialize file paths
        self.csv_file = self.base_path / "immobiliare.csv"
        if self.save_json:
            self.json_file = self.base_path / "immobiliare.json"
        
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
        # Initialize JSON file if enabled
        if self.save_json and not self.json_file.exists():
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump([], f)
            print(f"Initialized JSON file: {self.json_file}")
        
        # Initialize CSV file with RealEstate model fields
        if not self.csv_file.exists():
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=RealEstate.__dataclass_fields__.keys())
                writer.writeheader()
            print(f"Initialized CSV file: {self.csv_file}")
    
    def _convert_newlines(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert newlines in string fields to \n."""
        return {k: v.replace('\n', '\\n') if isinstance(v, str) else v 
                for k, v in data.items()}
    
    def append_data(self, data: List[Dict[str, Any]]) -> bool:
        """Append data to both JSON and CSV files."""
        if not data:
            print("No data to append")
            return False
        
        # Convert newlines in string fields
        cleaned_data = [self._convert_newlines(item) for item in data]
        
        # Convert raw data to RealEstate objects
        real_estate_objects = [RealEstate.from_dict(item) for item in cleaned_data]
            
        json_success = True
        if self.save_json:
            json_success = self._append_json(cleaned_data)
        
        csv_success = self._append_csv(real_estate_objects)
        
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
                json.dump(existing_data, f, ensure_ascii=False)
            
            print(f"Appended {len(data)} records to JSON file: {self.json_file}")
            return True
            
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to append JSON data: {e}")
            return False
    
    def _append_csv(self, data: List[RealEstate]) -> bool:
        """Append data to the CSV file."""
        try:
            # Open file in append mode
            with open(self.csv_file, "a", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=RealEstate.__dataclass_fields__.keys())
                
                # Write the data
                writer.writerows([item.to_dict() for item in data])
            
            print(f"Appended {len(data)} records to CSV file: {self.csv_file}")
            return True
            
        except IOError as e:
            print(f"Warning: Failed to append CSV data: {e}")
            return False
    
    def load_data(self) -> List[RealEstate]:
        """Load all real estate data from the CSV file."""
        try:
            with open(self.csv_file, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                return [RealEstate.from_dict(row) for row in reader]
        except IOError as e:
            raise StorageError(f"Failed to load CSV data: {e}")

class MongoDBStorage(DataStorage):
    """MongoDB-based storage implementation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize MongoDB storage.
        
        Args:
            config_path: Optional path to MongoDB configuration file
        """
        self.config = self._load_config(config_path)
        self.client = self._create_client()
        self.db = self.client[self.config['database']]
        self.collection = self.db[self.config['collection']]
        print(f"Connected to MongoDB: {self.config['database']}.{self.config['collection']}")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load MongoDB configuration from file."""
        if config_path is None:
            config_path = Path(__file__).parent / 'config' / 'mongodb.yaml'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)['mongodb']
                
            # Validate required fields
            required_fields = ['username', 'password', 'host', 'port', 'database', 'collection']
            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                raise ConfigurationError(f"Missing required fields in MongoDB config: {missing_fields}")
            
            return config
            
        except FileNotFoundError:
            raise StorageError(f"MongoDB configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise StorageError(f"Invalid MongoDB configuration: {e}")
    
    def _create_client(self) -> MongoClient:
        """Create MongoDB client with configuration."""
        try:
            # Build connection string
            connection_string = self.config['connection_string'].format(
                username=self.config['username'],
                password=self.config['password'],
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database']
            )
            
            # Create client options
            client_options = {
                'authSource': self.config.get('auth_source', 'admin'),
                'ssl': self.config.get('ssl', False)
            }
            
            if self.config.get('replica_set'):
                client_options['replicaSet'] = self.config['replica_set']
            
            if self.config.get('auth_mechanism'):
                client_options['authMechanism'] = self.config['auth_mechanism']
            
            # Create and test client
            client = MongoClient(connection_string, **client_options)
            client.admin.command('ping')  # Test connection
            return client
            
        except ConnectionFailure as e:
            raise StorageError(f"Failed to connect to MongoDB: {e}")
        except Exception as e:
            raise StorageError(f"Error creating MongoDB client: {e}")
    
    def _convert_newlines(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert newlines in string fields to \n."""
        return {k: v.replace('\n', '\\n') if isinstance(v, str) else v 
                for k, v in data.items()}
    
    def append_data(self, data: List[Dict[str, Any]]) -> bool:
        """Insert data into MongoDB collection."""
        if not data:
            print("No data to append")
            return False
            
        try:
            # Convert newlines in string fields
            cleaned_data = [self._convert_newlines(item) for item in data]
            result = self.collection.insert_many(cleaned_data)
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