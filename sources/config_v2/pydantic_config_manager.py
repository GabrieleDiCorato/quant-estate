"""
Pydantic-based configuration manager for the quant-estate project.
"""

import logging
from pathlib import Path
from typing import Any
from functools import lru_cache

import yaml
from ..exceptions import ConfigurationError
from ..logging.logging_utils import setup_logging
from .settings import (
    ScrapersSettings, 
    MongoDBSettings, 
    MongoDBRootSettings,
    ScraperConfig,
    StorageSettings
)

config_files = {
    'logging': 'default_logging.yaml',
    'scrapers': 'default_scrapers.yaml', 
    'mongodb': 'mongodb.yaml'
}


class PydanticConfigManager:
    """Manages project-wide and connector-specific configurations using Pydantic models.

    Handles three types of configurations:
    - Logging configuration (unchanged - returns dict)
    - Scraper configurations (Pydantic models)
    - MongoDB configurations (Pydantic models)
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
        if not PydanticConfigManager._logging_setup:
            self._setup_logging()
            PydanticConfigManager._logging_setup = True
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized PydanticConfigManager with config directory: {self.config_dir}")
    
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
    def _load_yaml_config(self, config_type: str) -> dict[str, Any]:
        """Load a YAML configuration file with caching.
        
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
        
        if config_type not in config_files:
            raise ConfigurationError(f"Unknown configuration type: {config_type}")
        
        return self.config_dir / config_files[config_type]
    
    def get_logging_config(self) -> dict[str, Any]:
        """Get logging configuration (unchanged for backwards compatibility).
        
        Returns:
            Dictionary containing the logging configuration
        """
        return self._load_yaml_config('logging')
    
    @lru_cache(maxsize=32)
    def get_scrapers_config(self) -> ScrapersSettings:
        """Get scrapers configuration as Pydantic model.
        
        Returns:
            ScrapersSettings instance containing the scrapers configuration
        """
        yaml_config = self._load_yaml_config('scrapers')
        try:
            # BaseSettings will automatically read from environment variables
            # We need to provide YAML data as _init_kwargs or merge manually
            import os
            
            # Create base settings that will read from environment
            settings = ScrapersSettings()
            
            # Now we need to apply YAML values for any settings not overridden by env vars
            # This is a bit complex with nested objects, so let's use a different approach
            
            # Build the configuration by merging YAML and environment variables
            merged_config = yaml_config.copy()
            
            # Check for environment overrides and apply them
            env_overrides = {}
            
            # Check for top-level scraper settings
            if 'SCRAPERS_IMMOBILIARE_ENABLED' in os.environ:
                if 'immobiliare' not in merged_config:
                    merged_config['immobiliare'] = {}
                merged_config['immobiliare']['enabled'] = os.environ['SCRAPERS_IMMOBILIARE_ENABLED'].lower() == 'true'
            
            if 'SCRAPERS_IMMOBILIARE_BASE_URL' in os.environ:
                if 'immobiliare' not in merged_config:
                    merged_config['immobiliare'] = {}
                merged_config['immobiliare']['base_url'] = os.environ['SCRAPERS_IMMOBILIARE_BASE_URL']
            
            # Check for request settings
            if 'SCRAPERS_REQUEST_MIN_DELAY' in os.environ:
                if 'immobiliare' not in merged_config:
                    merged_config['immobiliare'] = {}
                if 'request_settings' not in merged_config['immobiliare']:
                    merged_config['immobiliare']['request_settings'] = {}
                merged_config['immobiliare']['request_settings']['min_delay'] = int(os.environ['SCRAPERS_REQUEST_MIN_DELAY'])
            
            if 'SCRAPERS_REQUEST_MAX_DELAY' in os.environ:
                if 'immobiliare' not in merged_config:
                    merged_config['immobiliare'] = {}
                if 'request_settings' not in merged_config['immobiliare']:
                    merged_config['immobiliare']['request_settings'] = {}
                merged_config['immobiliare']['request_settings']['max_delay'] = int(os.environ['SCRAPERS_REQUEST_MAX_DELAY'])
            
            # Check for storage settings
            if 'SCRAPERS_STORAGE_TYPE' in os.environ:
                if 'immobiliare' not in merged_config:
                    merged_config['immobiliare'] = {}
                if 'storage_settings' not in merged_config['immobiliare']:
                    merged_config['immobiliare']['storage_settings'] = {}
                merged_config['immobiliare']['storage_settings']['type'] = os.environ['SCRAPERS_STORAGE_TYPE']
            
            return ScrapersSettings.model_validate(merged_config)
            
        except Exception as e:
            raise ConfigurationError(f"Invalid scrapers configuration: {e}")
    
    @lru_cache(maxsize=32)
    def get_mongodb_config(self) -> MongoDBSettings:
        """Get MongoDB configuration as Pydantic model.
        
        Returns:
            MongoDBSettings instance containing the MongoDB configuration
        """
        yaml_config = self._load_yaml_config('mongodb')
        try:
            import os
            
            # Handle both root structure and direct structure
            mongodb_data = yaml_config.get('mongodb', yaml_config) if 'mongodb' in yaml_config else yaml_config
            
            # Merge YAML config with environment variables
            merged_config = mongodb_data.copy()
            
            # Check for environment overrides
            env_mappings = {
                'MONGODB_HOST': 'host',
                'MONGODB_DATABASE': 'database',
                'MONGODB_COLLECTION': 'collection',
                'MONGODB_DB_QUERY': 'db_query',
                'MONGODB_USERNAME': 'username',
                'MONGODB_PASSWORD': 'password',
                'MONGODB_AUTH_SOURCE': 'auth_source',
                'MONGODB_AUTH_MECHANISM': 'auth_mechanism',
                'MONGODB_CONNECTION_STRING': 'connection_string',
                'MONGODB_REPLICA_SET': 'replica_set',
            }
            
            # Apply string/simple overrides
            for env_var, config_key in env_mappings.items():
                if env_var in os.environ:
                    merged_config[config_key] = os.environ[env_var]
            
            # Apply boolean overrides
            if 'MONGODB_SSL' in os.environ:
                merged_config['ssl'] = os.environ['MONGODB_SSL'].lower() == 'true'
            
            # Apply integer overrides
            if 'MONGODB_MAX_POOL_SIZE' in os.environ:
                merged_config['max_pool_size'] = int(os.environ['MONGODB_MAX_POOL_SIZE'])
            
            if 'MONGODB_MIN_POOL_SIZE' in os.environ:
                merged_config['min_pool_size'] = int(os.environ['MONGODB_MIN_POOL_SIZE'])
            
            if 'MONGODB_MAX_IDLE_TIME_MS' in os.environ:
                merged_config['max_idle_time_ms'] = int(os.environ['MONGODB_MAX_IDLE_TIME_MS'])
            
            # Apply write concern overrides
            if 'MONGODB_WRITE_CONCERN_W' in os.environ or 'MONGODB_WRITE_CONCERN_WTIMEOUT' in os.environ:
                if 'write_concern' not in merged_config:
                    merged_config['write_concern'] = {}
                
                if 'MONGODB_WRITE_CONCERN_W' in os.environ:
                    merged_config['write_concern']['w'] = int(os.environ['MONGODB_WRITE_CONCERN_W'])
                
                if 'MONGODB_WRITE_CONCERN_WTIMEOUT' in os.environ:
                    merged_config['write_concern']['wtimeout'] = int(os.environ['MONGODB_WRITE_CONCERN_WTIMEOUT'])
            
            return MongoDBSettings.model_validate(merged_config)
            
        except Exception as e:
            raise ConfigurationError(f"Invalid MongoDB configuration: {e}")
    
    def get_connector_config(self, connector: str) -> ScraperConfig:
        """Get configuration for a specific connector as Pydantic model.
        
        Args:
            connector: Name of the connector
            
        Returns:
            ScraperConfig instance containing the connector configuration
        """
        scrapers_config = self.get_scrapers_config()
        
        if not hasattr(scrapers_config, connector):
            raise ConfigurationError(f"Configuration for connector '{connector}' not found")
        
        return getattr(scrapers_config, connector)
    
    def get_storage_config(self, connector: str) -> dict[str, Any]:
        """Get storage configuration for a specific connector.
        
        Args:
            connector: Name of the connector
            
        Returns:
            Dictionary containing the storage configuration
        """
        connector_config = self.get_connector_config(connector)
        
        try:
            storage_config = connector_config.storage_settings.model_dump()
            storage_type = storage_config['type']
            
            # Merge MongoDB-specific config if needed
            if storage_type == 'mongodb':
                mongodb_config = self.get_mongodb_config()
                storage_config['settings'] = mongodb_config.model_dump()
                self.logger.info(f"Merged MongoDB configuration for connector '{connector}'")
            else:
                # For file storage, use the file settings
                storage_config['settings'] = storage_config['file']
            
            return storage_config
            
        except Exception as e:
            raise ConfigurationError(f"Error processing storage configuration for '{connector}': {e}")
    
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._load_yaml_config.cache_clear()
        self.get_scrapers_config.cache_clear()
        self.get_mongodb_config.cache_clear()
        self.logger.info("Configuration cache cleared")
