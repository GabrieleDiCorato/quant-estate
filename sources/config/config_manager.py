"""
Pydantic-based configuration manager for the quant-estate project.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from sources.exceptions import ConfigurationError

if TYPE_CHECKING:
    from sources.config.model.scraper_settings import (
        ScraperImmobiliareIdSettings,
        ScraperImmobiliareListingSettings,
    )
    from sources.config.model.storage_settings import StorageSettings

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Configuration manager for the QuantEstate project.

    Config file modifications at runtime will NOT be detected
    """

    def __init__(self) -> None:
        """Initialize ConfigManager with environment validation."""
        self._validate_environment()
        self._env: str = os.getenv("QE_ENV", "dev")
        self._conf_folder: str = os.getenv("QE_CONF_FOLDER", "sources/resources")
        self._project_root: Path = Path(__file__).parent.parent.parent

    def _validate_environment(self) -> None:
        """Validate required environment variables."""
        if not os.getenv("QE_ENV"):
            logger.info("QE_ENV not set, using default: 'dev'")
        if not os.getenv("QE_CONF_FOLDER"):
            logger.info("QE_CONF_FOLDER not set, using default: 'sources/resources'")

    def _get_env_file_path(self, config_type: str) -> Path:
        """Get environment file path for specific config type.

        Args:
            config_type: Configuration type identifier

        Returns:
            Path: Absolute path to environment file

        Raises:
            ConfigurationError: If environment file doesn't exist
        """
        env_file_path = self._project_root / self._conf_folder / f"{config_type}.{self._env}.env"

        if not env_file_path.exists():
            logger.warning(f"Environment file not found: {env_file_path}")

        return env_file_path

    def get_storage_config(self) -> StorageSettings:
        """Load storage configuration based on environment variables.

        Returns:
            StorageSettings: Configured storage settings instance

        Raises:
            ConfigurationError: If configuration loading fails
        """
        env_file_path = self._get_env_file_path("storage")
        return self._get_storage_config(env_file_path)

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_storage_config(env_file_path) -> StorageSettings:
        try:
            from sources.config.model.storage_settings import StorageSettings

            settings = StorageSettings(_env_file=env_file_path)
            logger.info(f"Loaded storage config from [{env_file_path}]: [{settings}]")
            return settings
        except Exception as e:
            logger.error(f"Failed to load storage configuration: {e}")
            raise ConfigurationError(f"Storage configuration error: {e}") from e

    def get_scraper_id_config(self) -> ScraperImmobiliareIdSettings:
        """Load scraper ID configuration based on environment variables.

        Returns:
            ScraperImmobiliareIdSettings: Configured scraper ID settings instance

        Raises:
            ConfigurationError: If configuration loading fails
        """
        env_file_path = self._get_env_file_path("scraper_imm_id")
        return self._get_scraper_id_config(env_file_path)

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_scraper_id_config(env_file_path) -> ScraperImmobiliareIdSettings:
        try:
            from sources.config.model.scraper_settings import ScraperImmobiliareIdSettings

            settings = ScraperImmobiliareIdSettings(_env_file=env_file_path)
            logger.info(f"Loaded scraper ID config from [{env_file_path}]: [{settings}]")
            return settings
        except Exception as e:
            logger.error(f"Failed to load scraper ID configuration: {e}")
            raise ConfigurationError(f"Scraper ID configuration error: {e}") from e

    def get_scraper_listing_config(self) -> ScraperImmobiliareListingSettings:
        """Load scraper listing configuration based on environment variables.

        Returns:
            ScraperImmobiliareListingSettings: Configured scraper listing settings instance

        Raises:
            ConfigurationError: If configuration loading fails
        """
        env_file_path = self._get_env_file_path("scraper_imm_listing")
        return self._get_scraper_listing_config(env_file_path)

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_scraper_listing_config(env_file_path) -> ScraperImmobiliareListingSettings:
        try:
            from sources.config.model.scraper_settings import ScraperImmobiliareListingSettings

            settings = ScraperImmobiliareListingSettings(_env_file=env_file_path)
            logger.info(f"Loaded scraper listing config from [{env_file_path}]: [{settings}]")
            return settings
        except Exception as e:
            logger.error(f"Failed to load scraper listing configuration: {e}")
            raise ConfigurationError(f"Scraper listing configuration error: {e}") from e

    def invalidate_caches(self) -> None:
        """Clear configuration cache to force reload on next access.

        This method clears all cached configuration objects, forcing them to be
        reloaded from environment variables and files on the next access.
        """
        self._get_storage_config.cache_clear()
        self._get_scraper_id_config.cache_clear()
        self._get_scraper_listing_config.cache_clear()
        logger.info("Configuration cache cleared - settings will be reloaded on next access")
