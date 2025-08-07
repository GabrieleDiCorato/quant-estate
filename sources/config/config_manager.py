"""
Pydantic-based configuration manager for the quant-estate project.
"""
import __future__
import logging
import os
from pathlib import Path
from functools import lru_cache

from sources.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class ConfigManager:
    """Configuration manager for the QuantEstate project."""

    def __init__(self):
        """Initialize ConfigManager with environment validation."""
        self._validate_environment()
        self._env = os.getenv("QE_ENV", "dev")
        self._conf_folder = os.getenv("QE_CONF_FOLDER", "sources/resources")
        self._project_root = Path(__file__).parent.parent.parent

    def _validate_environment(self) -> None:
        """Validate required environment variables."""
        if not os.getenv("QE_ENV"):
            logger.warning("QE_ENV not set, defaulting to 'dev'")
        if not os.getenv("QE_CONF_FOLDER"):
            logger.warning("QE_CONF_FOLDER not set, defaulting to 'sources/resources'")

    def _get_env_file_path(self, config_type: str) -> str:
        """Get environment file path for specific config type."""
        env_file_path = (
            self._project_root / self._conf_folder / f"{config_type}.{self._env}.env"
        )
        return str(env_file_path)

    # @lru_cache(maxsize=1)
    def get_storage_config(self) -> "StorageSettings":
        """Load storage configuration based on environment variables."""
        from .model.storage_settings import StorageSettings

        # Override the env_file in model_config at runtime
        env_file_path = self._get_env_file_path("storage")

        # Create settings with runtime env file path
        settings = StorageSettings(_env_file=env_file_path)
        logger.info(f"Loaded storage config from [{env_file_path}]: [{settings}]")
        return settings

        # @lru_cache(maxsize=1)

    def get_scraper_id_config(self) -> "ScraperImmobiliareIdSettings":
        """Load storage configuration based on environment variables."""
        from .model.scraper_settings import ScraperImmobiliareIdSettings

        # Override the env_file in model_config at runtime
        env_file_path = self._get_env_file_path("scraper_imm_id")

        # Create settings with runtime env file path
        settings = ScraperImmobiliareIdSettings(_env_file=env_file_path)
        logger.info(f"Loaded scraper ID config from [{env_file_path}]: [{settings}]")
        return settings

    def get_scraper_listing_config(self) -> "ScraperImmobiliareListingSettings":
        """Load storage configuration based on environment variables."""
        from .model.scraper_settings import ScraperImmobiliareListingSettings

        # Override the env_file in model_config at runtime
        env_file_path = self._get_env_file_path("scraper_imm_listing")

        # Create settings with runtime env file path
        settings = ScraperImmobiliareListingSettings(_env_file=env_file_path)
        logger.info(f"Loaded scraper listing config from [{env_file_path}]: [{settings}]")
        return settings
