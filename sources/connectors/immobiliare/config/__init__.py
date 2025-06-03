"""
Configuration for the immobiliare connector.
"""

from pathlib import Path
import yaml

def load_config() -> dict:
    """Load the default configuration."""
    config_path = Path(__file__).parent / 'default.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Load the default configuration
config = load_config() 