"""
Pydantic settings models for the quant-estate project.
"""

from __future__ import annotations

from typing import Literal, Optional
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class RequestSettings(BaseSettings):
    """Request settings for scrapers."""
    model_config = SettingsConfigDict(
        extra='forbid',
        validate_default=True,
        env_prefix='SCRAPERS_REQUEST_',
        case_sensitive=False
    )
    
    min_delay: int = Field(default=10, ge=1, description="Minimum delay between requests in seconds")
    max_delay: int = Field(default=20, ge=1, description="Maximum delay between requests in seconds")
    
    @field_validator('max_delay')
    @classmethod
    def max_delay_must_be_greater_than_min(cls, v, info):
        if 'min_delay' in info.data and v < info.data['min_delay']:
            raise ValueError('max_delay must be greater than or equal to min_delay')
        return v


class FileStorageSettings(BaseSettings):
    """File storage settings."""
    model_config = SettingsConfigDict(
        extra='forbid',
        validate_default=True,
        env_prefix='SCRAPERS_FILE_STORAGE_',
        case_sensitive=False
    )
    
    base_path: str = Field(default="data", description="Base path for file storage")


class MongoDBStorageSettings(BaseSettings):
    """MongoDB storage settings for scrapers."""
    model_config = SettingsConfigDict(
        extra='forbid',
        validate_default=True,
        env_prefix='SCRAPERS_MONGODB_STORAGE_',
        case_sensitive=False
    )
    
    id_collection: str = Field(default="ids", description="Collection name for IDs")
    listing_collection: str = Field(default="listings", description="Collection name for listings")


class StorageSettings(BaseSettings):
    """Storage settings for scrapers."""
    model_config = SettingsConfigDict(
        extra='forbid',
        validate_default=True,
        env_prefix='SCRAPERS_STORAGE_',
        case_sensitive=False
    )
    
    type: Literal["file", "mongodb"] = Field(default="mongodb", description="Storage type")
    file: FileStorageSettings = Field(default_factory=FileStorageSettings)
    mongodb: MongoDBStorageSettings = Field(default_factory=MongoDBStorageSettings)


class ScraperConfig(BaseSettings):
    """Configuration for a scraper."""
    model_config = SettingsConfigDict(
        extra='forbid',
        validate_default=True,
        env_prefix='SCRAPERS_',
        case_sensitive=False
    )
    
    enabled: bool = Field(default=True, description="Enable or disable the connector")
    base_url: str = Field(description="Base URL for the scraper")
    request_settings: RequestSettings = Field(default_factory=RequestSettings)
    storage_settings: StorageSettings = Field(default_factory=StorageSettings)


class ScrapersSettings(BaseSettings):
    """Scrapers configuration settings."""
    model_config = SettingsConfigDict(
        extra='forbid',
        validate_default=True,
        env_prefix='SCRAPERS_',
        case_sensitive=False
    )
    
    immobiliare: ScraperConfig = Field(
        default_factory=lambda: ScraperConfig(base_url="https://www.immobiliare.it")
    )


class WriteConcernSettings(BaseModel):
    """MongoDB write concern settings."""
    w: int = Field(default=1, description="Write acknowledgment level")
    wtimeout: int = Field(default=5000, description="Write timeout in milliseconds")


class MongoDBSettings(BaseSettings):
    """MongoDB configuration settings."""
    model_config = SettingsConfigDict(
        extra='forbid',
        validate_default=True,
        env_prefix='MONGODB_',
        case_sensitive=False
    )
    
    # Connection settings
    connection_string: str = Field(
        default="mongodb+srv://{username}:{password}@{host}:{port}/{database}",
        description="MongoDB connection string"
    )
    host: str = Field(default="", description="MongoDB host")
    database: str = Field(default="", description="Database name")
    collection: str = Field(default="", description="Collection name")
    db_query: str = Field(default="", description="Database query")
    
    # Authentication settings
    username: str = Field(default="", description="MongoDB username")
    password: str = Field(default="", description="MongoDB password")
    auth_source: str = Field(default="admin", description="Authentication database")
    auth_mechanism: str = Field(default="SCRAM-SHA-256", description="Authentication mechanism")
    
    # Security settings
    ssl: bool = Field(default=False, description="Use SSL/TLS connection")
    replica_set: Optional[str] = Field(default=None, description="Replica set name")
    
    # Connection pool settings
    max_pool_size: int = Field(default=100, ge=1, description="Maximum connection pool size")
    min_pool_size: int = Field(default=0, ge=0, description="Minimum connection pool size")
    max_idle_time_ms: int = Field(default=60000, ge=0, description="Maximum idle time in milliseconds")
    
    # Write concern settings
    write_concern: WriteConcernSettings = Field(default_factory=WriteConcernSettings)
    
    @field_validator('max_pool_size')
    @classmethod
    def max_pool_size_must_be_greater_than_min(cls, v, info):
        if 'min_pool_size' in info.data and v < info.data['min_pool_size']:
            raise ValueError('max_pool_size must be greater than or equal to min_pool_size')
        return v


class MongoDBRootSettings(BaseSettings):
    """Root MongoDB settings wrapper."""
    model_config = SettingsConfigDict(
        extra='forbid',
        validate_default=True
    )
    
    mongodb: MongoDBSettings = Field(default_factory=MongoDBSettings)
