from typing import List, Dict, Any
import os
from pathlib import Path
from datetime import datetime

from .storage import FileStorage
from .models import RealEstate
from .exceptions import StorageError
from .scraper import ImmobiliareScraper

def test_file_storage():
    """Test the FileStorage implementation with sample data."""
    
    # Create a test directory in the current working directory
    test_dir = Path("test_data") / f"immobiliare_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Initialize storage with test directory
        storage = FileStorage(base_path=str(test_dir))
        print(f"Storage initialized at: {storage.base_path}")
        
        # Sample data
        sample_data: List[Dict[str, Any]] = [
            {
                "id": "1",
                "title": "Test Property 1",
                "price": 300000,
                "surface": 120.5,
                "rooms": 3,
                "bathrooms": 2,
                "description": "A beautiful test property",
                "url": "https://example.com/1"
            },
            {
                "id": "2",
                "title": "Test Property 2",
                "price": 450000,
                "surface": 180.0,
                "rooms": 4,
                "bathrooms": 3,
                "description": "Another test property",
                "url": "https://example.com/2"
            }
        ]
        
        # Test appending data
        print("\nTesting data append...")
        success = storage.append_data(sample_data)
        print(f"Append successful: {success}")
        
        # Test loading data
        print("\nTesting data load...")
        loaded_data = storage.load_data()
        print(f"Loaded {len(loaded_data)} records")
        
        # Print loaded data
        print("\nLoaded data:")
        for estate in loaded_data:
            print(f"\nProperty: {estate.title}")
            print(f"Price: €{estate.price:,}")
            print(f"Surface: {estate.surface} m²")
            print(f"Rooms: {estate.rooms}")
            print(f"Bathrooms: {estate.bathrooms}")
        
        # Test appending more data
        print("\nTesting append of additional data...")
        additional_data = [
            {
                "id": "3",
                "title": "Test Property 3",
                "price": 550000,
                "surface": 200.0,
                "rooms": 5,
                "bathrooms": 3,
                "description": "A third test property",
                "url": "https://example.com/3"
            }
        ]
        success = storage.append_data(additional_data)
        print(f"Additional append successful: {success}")
        
        # Verify final data
        final_data = storage.load_data()
        print(f"\nFinal record count: {len(final_data)}")
        
    except StorageError as e:
        print(f"Storage error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Clean up test directory
        if test_dir.exists():
            for file in test_dir.glob("*"):
                file.unlink()
            test_dir.rmdir()
            print(f"\nCleaned up test directory: {test_dir}")

if __name__ == "__main__":
    test_file_storage()

# Create a file storage instance
storage = FileStorage()

# Create and run the scraper with the storage
scraper = ImmobiliareScraper(
    url="https://www.immobiliare.it/vendita-case/milano/",
    storage=storage,
    get_data_of_following_pages=True,
    max_pages=2
)

# Print some basic stats
print(f"Scraped {len(scraper.real_estates)} properties")
print(f"Failed pages: {scraper.failed_pages}") 