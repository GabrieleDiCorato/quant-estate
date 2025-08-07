"""
Pydantic-based configuration manager for the quant-estate project.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from functools import lru_cache
from typing import TYPE_CHECKING

from sources.exceptions import ConfigurationError

if TYPE_CHECKING:
    from sources.config.model.storage_settings import StorageSettings
    from sources.config.model.scraper_settings import ScraperImmobiliareIdSettings, ScraperImmobiliareListingSettings

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
        env_file_path = (
            self._project_root / self._conf_folder / f"{config_type}.{self._env}.env"
        )

        if not env_file_path.exists():
            logger.warning(f"Environment file not found: {env_file_path}")

        return env_file_path

    @lru_cache(maxsize=1)
    def get_storage_config(self) -> StorageSettings:
        """Load storage configuration based on environment variables.
        
        Returns:
            StorageSettings: Configured storage settings instance
            
        Raises:
            ConfigurationError: If configuration loading fails
        """
        try:
            from sources.config.model.storage_settings import StorageSettings

            env_file_path = self._get_env_file_path("storage")

            # Set environment variable for Pydantic to pick up
            os.environ["STORAGE_ENV_FILE"] = str(env_file_path)

            settings = StorageSettings()
            logger.info(f"Loaded storage config from [{env_file_path}]: [{settings}]")
            return settings
        except Exception as e:
            logger.error(f"Failed to load storage configuration: {e}")
            raise ConfigurationError(f"Storage configuration error: {e}") from e

    @lru_cache(maxsize=1)
    def get_scraper_id_config(self) -> ScraperImmobiliareIdSettings:
        """Load scraper ID configuration based on environment variables.
        
        Returns:
            ScraperImmobiliareIdSettings: Configured scraper ID settings instance
            
        Raises:
            ConfigurationError: If configuration loading fails
        """
        try:
            from sources.config.model.scraper_settings import ScraperImmobiliareIdSettings

            env_file_path = self._get_env_file_path("scraper_imm_id")

            # Set environment variable for Pydantic to pick up
            os.environ["SCRAPER_IMM_ID_ENV_FILE"] = str(env_file_path)

            settings = ScraperImmobiliareIdSettings()
            logger.info(f"Loaded scraper ID config from [{env_file_path}]: [{settings}]")
            return settings
        except Exception as e:
            logger.error(f"Failed to load scraper ID configuration: {e}")
            raise ConfigurationError(f"Scraper ID configuration error: {e}") from e

    @lru_cache(maxsize=1)
    def get_scraper_listing_config(self) -> ScraperImmobiliareListingSettings:
        """Load scraper listing configuration based on environment variables.
        
        Returns:
            ScraperImmobiliareListingSettings: Configured scraper listing settings instance
            
        Raises:
            ConfigurationError: If configuration loading fails
        """
        try:
            from sources.config.model.scraper_settings import ScraperImmobiliareListingSettings

            env_file_path = self._get_env_file_path("scraper_imm_listing")

            # Set environment variable for Pydantic to pick up
            os.environ["SCRAPER_IMM_LISTING_ENV_FILE"] = str(env_file_path)

            settings = ScraperImmobiliareListingSettings()
            logger.info(f"Loaded scraper listing config from [{env_file_path}]: [{settings}]")
            return settings
        except Exception as e:
            logger.error(f"Failed to load scraper listing configuration: {e}")
            raise ConfigurationError(f"Scraper listing configuration error: {e}") from e
