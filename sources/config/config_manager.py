"""
Configuration manager for the quant-estate project.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union

from ..logging.logging import get_module_logger
from ..exceptions import ConfigurationError

logger = get_module_logger()

class ConfigManager:
    """Manages project-wide and connector-specific configurations."""
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Optional path to the configuration directory.
                       If None, uses the default config directory.
        """
        if config_dir is None:
            # Use the config directory relative to this file
            config_dir = Path(__file__).parent.absolute()
        self.config_dir = Path(config_dir)
        self._configs: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Initialized ConfigManager with config directory: {self.config_dir}")
    
    def load_config(self, name: str, connector: Optional[str] = None) -> Dict[str, Any]:
        """Load a configuration file.
        
        Args:
            name: Name of the configuration file (without extension)
            connector: Optional connector name to load connector-specific config
            
        Returns:
            Dict containing the configuration
            
        Raises:
            ConfigurationError: If the configuration file doesn't exist or is invalid
        """
        # Create cache key
        cache_key = f"{connector}.{name}" if connector else name
        
        if cache_key in self._configs:
            return self._configs[cache_key]
        
        # Determine config path
        if connector:
            config_path = self.config_dir / 'connectors' / connector / f"{name}.yaml"
        else:
            config_path = self.config_dir / f"{name}.yaml"
            
        logger.debug(f"Loading configuration from {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            if not isinstance(config, dict):
                raise ConfigurationError(f"Configuration file {name} must contain a dictionary")
            self._configs[cache_key] = config
            logger.info(f"Successfully loaded configuration: {cache_key}")
            return config
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file {config_path}: {e}")
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get the logging configuration.
        
        Returns:
            Dict containing the logging configuration
            
        Raises:
            ConfigurationError: If the logging configuration is invalid
        """
        return self.load_config('logging')
    
    def get_connector_config(self, connector: str) -> Dict[str, Any]:
        """Get configuration for a specific connector.
        
        Args:
            connector: Name of the connector
            
        Returns:
            Dict containing the connector configuration
            
        Raises:
            ConfigurationError: If the connector configuration is invalid
        """
        return self.load_config('default', connector)
    
    def get_storage_config(self, connector: str) -> Dict[str, Any]:
        """Get storage configuration for a specific connector.
        
        Args:
            connector: Name of the connector
            
        Returns:
            Dict containing the storage configuration
            
        Raises:
            ConfigurationError: If the storage configuration is invalid
        """
        config = self.get_connector_config(connector)
        try:
            storage_config = config['storage_settings']
            storage_type = storage_config['type']
            
            # If MongoDB storage is selected, merge with MongoDB config
            if storage_type == 'mongodb':
                mongodb_config = self.load_config('mongodb', connector)
                storage_config['settings'] = mongodb_config['mongodb']
                logger.info("Merged MongoDB configuration with storage settings")
            
            return storage_config
        except KeyError as e:
            raise ConfigurationError(f"Missing required storage configuration key: {e}")
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for a specific module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Dict containing the module configuration
            
        Raises:
            ConfigurationError: If the module configuration is invalid
        """
        config = self.get_logging_config()
        try:
            return config['handlers']['modules'][module_name]
        except KeyError as e:
            raise ConfigurationError(f"Missing required module configuration key: {e}") 