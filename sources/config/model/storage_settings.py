from enum import Enum
import os
from pathlib import Path
from pydantic import BaseModel, Field, computed_field, field_validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from sources.exceptions import ConfigurationError


class StorageType(Enum):
    """Enum for storage types."""
    FILE = "file"
    MONGODB = "mongodb"

    def __str__(self):
        return self.value


class CsvStorageSettings(BaseModel):
    """File storage settings for scrapers."""

    base_path: Path = Field(default=Path.cwd() / "data", description="Base path for file storage")


class MongoStorageSettings(BaseModel):
    """MongoDB storage settings for scrapers."""

    # SRV does not require a port
    connection_string: SecretStr = Field(
        default=SecretStr("mongodb://localhost:27017"),
        description="MongoDB connection string"
    )

    database: str = Field(default="quant_estate", description="MongoDB database name")
    collection_ids: str = Field(default="ids", description="Collection name for storing IDs")
    collection_listings: str = Field(default="listings", description="Collection name for storing listings")

    max_pool_size: int = Field(default=100, description="Maximum pool size for MongoDB connections")
    min_pool_size: int = Field(default=10, description="Minimum pool size for MongoDB connections")
    max_idle_time_ms: int = Field(default=60000, description="Maximum idle time for MongoDB connections in milliseconds")

    wtimeout: int = Field(default=5000, description="Timeout for MongoDB operations in milliseconds")


class StorageSettings(BaseSettings):
    """Storage settings """

    env: str | None = os.getenv("QE_ENV")
    if not env:
        raise ConfigurationError("QE_ENV environment variable is not set")

    conf_folder: str | None = os.getenv("QE_CONF_FOLDER")
    if not conf_folder:
        raise ConfigurationError("QE_CONF_FOLDER environment variable is not set")

    model_config = SettingsConfigDict(
        extra="forbid",
        validate_default=True,
        case_sensitive=False,
        use_enum_values=True,
        env_prefix="STORAGE_",
        env_file_encoding="utf-8",
        env_file=os.path.join(Path.cwd(), conf_folder, f"config.{env}.env"),
        env_ignore_empty=True,
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
    )

    storage_type: StorageType = Field(default=StorageType.FILE, description="Storage type (file or mongodb)")
    file_settings: CsvStorageSettings = Field(default_factory=CsvStorageSettings, description="File storage settings")
    mongodb_settings: MongoStorageSettings = Field(default_factory=MongoStorageSettings, description="MongoDB storage settings")