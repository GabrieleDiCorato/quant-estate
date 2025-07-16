"""
Configuration manager for the quant-estate project.
"""

import logging
from pathlib import Path
from typing import Any
from functools import lru_cache

import yaml
from ..exceptions import ConfigurationError
from ..logging.logging_utils import setup_logging


class ConfigManager:
    """Manages project-wide and connector-specific configurations.

    Handles three types of configurations:
    - Logging configuration
    - Scraper configurations  
    - MongoDB configurations
    """
    
    _logging_setup = False
    
    def __init__(self, config_dir: Path | str | None = None):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Optional path to the configuration directory.
                       If None, uses the default config directory.
        """
        self.config_dir = Path(config_dir) if config_dir else self._get_default_config_dir()
        
        # Setup logging once globally
        if not ConfigManager._logging_setup:
            self._setup_logging()
            ConfigManager._logging_setup = True
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized ConfigManager with config directory: {self.config_dir}")
    
    def _get_default_config_dir(self) -> Path:
        """Get the default configuration directory."""
        return Path(__file__).parent / 'default'
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        try:
            logging_config_path = self.config_dir / 'default_logging.yaml'
            setup_logging(logging_config_path)
        except Exception as e:
            # Fallback to basic logging if config fails
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
            )
            logging.getLogger(__name__).warning(f"Failed to setup logging from config: {e}")
    
    @lru_cache(maxsize=32)
    def load_config(self, config_type: str) -> dict[str, Any]:
        """Load a configuration file with caching.
        
        Args:
            config_type: Type of configuration ('logging', 'scrapers', 'mongodb')
            
        Returns:
            Dictionary containing the configuration
            
        Raises:
            ConfigurationError: If the configuration file doesn't exist or is invalid
        """
        config_path = self._get_default_config_path(config_type)
        
        self.logger.debug(f"Loading {config_type} configuration from {config_path}")
        
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not isinstance(config, dict):
                raise ConfigurationError(f"Configuration file {config_path.name} must contain a dictionary")
            
            self.logger.info(f"Successfully loaded {config_type} configuration from {config_path.name}")
            return config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file {config_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading configuration file {config_path}: {e}")
    
    def _get_default_config_path(self, config_type: str) -> Path:
        """Get the path to a default configuration file."""
        config_files = {
            'logging': 'default_logging.yaml',
            'scrapers': 'default_scrapers.yaml', 
            'mongodb': 'mongodb.yaml'
        }
        
        if config_type not in config_files:
            raise ConfigurationError(f"Unknown configuration type: {config_type}")
        
        return self.config_dir / config_files[config_type]
    
    def get_logging_config(self) -> dict[str, Any]:
        """Get logging configuration.
        
        Returns:
            Dictionary containing the logging configuration
        """
        return self.load_config('logging')
    
    def get_scrapers_config(self) -> dict[str, Any]:
        """Get scrapers configuration.
        
        Returns:
            Dictionary containing the scrapers configuration
        """
        return self.load_config('scrapers')
    
    def get_mongodb_config(self) -> dict[str, Any]:
        """Get MongoDB configuration.
        
        Returns:
            Dictionary containing the MongoDB configuration
        """
        return self.load_config('mongodb')
    
    def get_connector_config(self, connector: str) -> dict[str, Any]:
        """Get configuration for a specific connector.
        
        Args:
            connector: Name of the connector
            
        Returns:
            Dictionary containing the connector configuration
        """
        scrapers_config = self.get_scrapers_config()
        
        if connector not in scrapers_config:
            raise ConfigurationError(f"Configuration for connector '{connector}' not found")
        
        return scrapers_config[connector]
    
    def get_storage_config(self, connector: str) -> dict[str, Any]:
        """Get storage configuration for a specific connector.
        
        Args:
            connector: Name of the connector
            
        Returns:
            Dictionary containing the storage configuration
        """
        connector_config = self.get_connector_config(connector)
        
        try:
            storage_config = connector_config['storage_settings'].copy()
            storage_type = storage_config['type']
            
            # Merge MongoDB-specific config if needed
            if storage_type == 'mongodb':
                mongodb_config = self.get_mongodb_config()
                storage_config['settings'] = mongodb_config['mongodb']
                self.logger.info(f"Merged MongoDB configuration for connector '{connector}'")
            
            return storage_config
            
        except KeyError as e:
            raise ConfigurationError(f"Missing required storage configuration key for '{connector}': {e}")
    
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self.load_config.cache_clear()
        self.logger.info("Configuration cache cleared") 