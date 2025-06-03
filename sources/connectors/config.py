"""
Configuration management for real estate data connectors.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Manages configuration for real estate data connectors."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Optional path to the configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        # Get the absolute path to the project root
        project_root = Path(__file__).parent.parent.parent
        return str(project_root / "sources" / "connectors" / "immobiliare" / "config" / "default.yaml")
    
    def _load_yaml_config(self, yaml_path: str) -> Dict[str, Any]:
        """Load configuration from a YAML file.
        
        Args:
            yaml_path: Path to the YAML configuration file
            
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Failed to load YAML config from {yaml_path}: {e}")
            return {}
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and connector-specific YAML files."""
        try:
            # Load base configuration
            if not os.path.exists(self.config_path):
                base_config = self._create_default_config()
            else:
                base_config = self._load_yaml_config(self.config_path)
            
            return base_config
                
        except Exception as e:
            print(f"Warning: Failed to load config from {self.config_path}: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create and save default configuration."""
        default_config = {
            "base_url": "https://www.immobiliare.it",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            },
            "request_settings": {
                "min_delay": 10,
                "max_delay": 30
            },
            "storage_settings": {
                "folder_name": "immobiliare_data",
                "default_json_filename": "immobiliare.json",
                "default_csv_filename": "immobiliare.csv",
                "date_format": "%Y-%m-%d",
                "save_json": True
            }
        }
        
        try:
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save default config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False)
                
            print(f"Created default configuration at {self.config_path}")
            
        except Exception as e:
            print(f"Warning: Failed to create default config: {e}")
        
        return default_config
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration."""
        return self.config.get('storage_settings', {})
    
    def get_request_settings(self) -> Dict[str, Any]:
        """Get request settings."""
        return self.config.get('request_settings', {})
    
    def get_connector_config(self, connector_name: str) -> Dict[str, Any]:
        """Get configuration for a specific connector.
        
        Args:
            connector_name: Name of the connector (e.g., 'immobiliare')
            
        Returns:
            Dict[str, Any]: Configuration for the specified connector
        """
        # Return the entire config as it's already connector-specific
        config = self.config.copy()
        
        # Ensure base_url is at the root level
        if 'base_url' not in config:
            raise ValueError("Configuration must include 'base_url'")
            
        return config
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        self.config.update(updates)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False)
                
        except Exception as e:
            print(f"Warning: Failed to save config updates: {e}") 