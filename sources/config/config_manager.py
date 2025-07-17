"""
Pydantic-based configuration manager for the quant-estate project.
"""

import logging
import os
from pathlib import Path
from functools import lru_cache

from pydantic import ValidationError
from ..exceptions import ConfigurationError
from .model.storage_settings import StorageSettings, CsvStorageSettings, MongoStorageSettings

logger = logging.getLogger(__name__)


class ConfigManager:
    """Configuration manager for the QuantEstate project.
    """

    @lru_cache(maxsize=1)
    def get_storage_config(self) -> StorageSettings:
        """Load storage configuration based on environment variables."""
        return StorageSettings()

    def reload_config(self) -> None:
        """Clear cached configuration to force reload on next access."""
        self.get_storage_config.cache_clear()
        logger.info("Configuration cache cleared")
