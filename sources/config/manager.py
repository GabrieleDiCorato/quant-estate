"""
Configuration manager for the quant-estate project.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union

from ..utils.logging import get_module_logger

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
            config_dir = Path(__file__).parent
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
            FileNotFoundError: If the configuration file doesn't exist
            yaml.YAMLError: If the configuration file is invalid
        """
        # Create cache key
        cache_key = f"{connector}.{name}" if connector else name
        
        if cache_key in self._configs:
            return self._configs[cache_key]
        
        # Determine config path
        if connector:
            config_path = self.config_dir.parent / 'connectors' / connector / 'config' / f"{name}.yaml"
        else:
            config_path = self.config_dir / f"{name}.yaml"
            
        logger.debug(f"Loading configuration from {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self._configs[cache_key] = config
            logger.info(f"Successfully loaded configuration: {cache_key}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in configuration file {config_path}: {e}")
            raise
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get the logging configuration.
        
        Returns:
            Dict containing the logging configuration
        """
        return self.load_config('logging')
    
    def get_connector_config(self, connector: str) -> Dict[str, Any]:
        """Get configuration for a specific connector.
        
        Args:
            connector: Name of the connector
            
        Returns:
            Dict containing the connector configuration
        """
        return self.load_config('default', connector)
    
    def get_storage_config(self, connector: str) -> Dict[str, Any]:
        """Get storage configuration for a specific connector.
        
        Args:
            connector: Name of the connector
            
        Returns:
            Dict containing the storage configuration
        """
        config = self.get_connector_config(connector)
        storage_config = config.get('storage_settings', {})
        
        # If MongoDB storage is selected, merge with MongoDB config
        if storage_config.get('type') == 'mongodb':
            try:
                mongodb_config = self.load_config('mongodb', connector)
                storage_config['settings'] = mongodb_config['mongodb']
                logger.info("Merged MongoDB configuration with storage settings")
            except FileNotFoundError:
                logger.error("MongoDB configuration not found")
                raise
            except KeyError as e:
                logger.error(f"Invalid MongoDB configuration: {e}")
                raise
        
        return storage_config
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for a specific module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Dict containing the module configuration
        """
        config = self.get_logging_config()
        return config.get('handlers', {}).get('modules', {}).get(module_name, {}) 