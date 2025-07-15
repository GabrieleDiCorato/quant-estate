"""
Configuration manager for the quant-estate project.
"""

import yaml
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping, MappingView
from typing import Any
from ..logging_utils.logging_mixin import LoggingMixin
from ..datamodel.enumerations import Source

from ..exceptions import ConfigurationError

class ConfigManager(LoggingMixin):
    """Manages project-wide and connector-specific configurations."""

    def __init__(self, config_dir: str | None = None):
        """Initialize the configuration manager.
        
        Args:
            config_dir: optional path to the configuration directory.
                       If None, uses the default config directory.
        """
        super().__init__()
        self.logger.info("Initializing ConfigManager")

        if config_dir is None:
            # Use the config directory relative to this file
            self.config_dir = Path(__file__).absolute() / "default"
        else:
            self.config_dir = Path(config_dir)

        self.logger.info("Loading configurations from directory: [%s]", self.config_dir)
        self._configs: Mapping[str, Any] = {}
        files = [f for f in self.config_dir.iterdir() if f.is_file() and f.suffix == '.yaml' and "template" not in f.name]
        for f in files:
            self.logger.debug("Loading configuration from [%s]", f.name)
            config: dict = yaml.safe_load(f.read_text(encoding='utf-8'))
            self.logger.debug("Loaded configuration from [%s]", f.name)
            self._configs.update(config)

        # Make it immutable
        self._configs = MappingProxyType(self._configs) 

        self.logger.info("Initialized ConfigManager with config directory: [%s]", self.config_dir)
        self.logger.debug("Available configurations:\n%s", yaml.dump(self._configs, default_flow_style=False))

    def get_logging_config(self) -> Mapping[str, Any]:
        """Get the logging configuration.
        
        Returns:
            Mapping containing the logging configuration
            
        Raises:
            ConfigurationError: If the logging configuration is missing
        """
        """Get an immutable view of the logging configuration."""
        if "logging" not in self._configs:
            raise ConfigurationError("Logging configuration not found. Expected 'logging' key")
        return self._configs["logging"]

    def get_connector_config(self, connector: Source) -> Mapping[str, Any]:
        """Get configuration for a specific connector.
        
        Args:
            connector: Name of the connector
            
        Returns:
            Dict containing the connector configuration
            
        Raises:
            ConfigurationError: If the connector configuration is missing
        """
        if connector.value not in self._configs:
            raise ConfigurationError(f"Connector configuration not found. Expected '{connector.value}' key")
        return self._configs[connector.value]

    def get_config(self) -> Mapping[str, Any]:
        """
        Get the complete configuration.
        """
        return self._configs
