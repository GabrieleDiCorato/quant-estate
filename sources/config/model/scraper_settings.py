from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict



class ImmobiliareScraperSettings(BaseModel):
    """Settings for Immobiliare scraper."""
    base_url: str = Field(default="https://www.immobiliare.it", description="Base URL for Immobiliare scraper")
    search_url: str = Field(default="/vendita-case/", description="Search URL for Immobiliare listings")
    listing_details_url: str = Field(default="/annunci/", description="URL pattern for listing details")
    max_pages: int = Field(default=10, description="Maximum number of pages to scrape")


class ScraperSettings(BaseSettings):
    """Settings for scrapers."""
    
    model_config = SettingsConfigDict(
        extra="forbid",
        validate_default=True,
        case_sensitive=False,
        use_enum_values=True,
        env_prefix="SCRAPER__",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
    )

    immobiliare: ImmobiliareScraperSettings = Field(default_factory=ImmobiliareScraperSettings, description="Settings for Immobiliare scraper")