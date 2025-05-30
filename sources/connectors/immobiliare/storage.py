import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List
from .models import RealEstate
from .exceptions import StorageError
from .config import config

class DataStorage:
    """Handles storage operations for real estate data."""
    
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
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the storage directory exists."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            print(f"Storage directory: {self.base_path}")
        except OSError as e:
            raise StorageError(f"Failed to create storage directory: {e}")
    
    def save_json(self, data: List[RealEstate], filename: str = None) -> None:
        """Save real estate data to a JSON file."""
        filename = filename or config.storage_settings.get("default_json_filename", "immobiliare.json")
        filepath = self.base_path / filename
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump([estate.to_dict() for estate in data], f, indent=4)
            print(f"Saved JSON to {filepath}")
        except (IOError, json.JSONDecodeError) as e:
            raise StorageError(f"Failed to save JSON data: {e}")
    
    def save_csv(self, data: List[RealEstate], filename: str = None) -> None:
        """Save real estate data to a CSV file."""
        filename = filename or config.storage_settings.get("default_csv_filename", "immobiliare.csv")
        filepath = self.base_path / filename
        
        if not data:
            print("No data to save")
            return
        
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = data[0].to_dict().keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for estate in data:
                    writer.writerow(estate.to_dict())
            print(f"Saved CSV to {filepath}")
        except IOError as e:
            raise StorageError(f"Failed to save CSV data: {e}")
    
    def load_json(self, filename: str = None) -> List[RealEstate]:
        """Load real estate data from a JSON file."""
        filename = filename or config.storage_settings.get("default_json_filename", "immobiliare.json")
        filepath = self.base_path / filename
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [RealEstate.from_dict(item) for item in data]
        except (IOError, json.JSONDecodeError) as e:
            raise StorageError(f"Failed to load JSON data: {e}")
    
    def load_csv(self, filename: str = None) -> List[RealEstate]:
        """Load real estate data from a CSV file."""
        filename = filename or config.storage_settings.get("default_csv_filename", "immobiliare.csv")
        filepath = self.base_path / filename
        
        try:
            with open(filepath, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                return [RealEstate.from_dict(row) for row in reader]
        except IOError as e:
            raise StorageError(f"Failed to load CSV data: {e}") 