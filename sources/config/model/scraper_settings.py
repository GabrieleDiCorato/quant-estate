from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def makeSettingsConfigDict(env_prefix: str = "SCRAPER__") -> SettingsConfigDict:
    """Create a SettingsConfigDict with common configuration."""
    return SettingsConfigDict(
        extra="forbid",
        validate_default=True,
        case_sensitive=False,
        use_enum_values=True,
        env_prefix=env_prefix,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
    )

class ScraperSettings(BaseSettings):
    """Base settings for scrapers."""

    min_delay: float = Field(default=1.0, description="Minimum delay between requests in seconds")
    max_delay: float = Field(default=3.0, description="Maximum delay between requests in seconds")
    headless: bool = Field(default=False, description="Run browser in headless mode")
    implicit_wait: int = Field(default=10, description="Implicit wait timeout for elements in seconds")
    page_load_timeout: int = Field(default=30, description="Page load timeout in seconds")
    window_size: tuple[int, int] = Field(default=(1366, 768), description="Browser window size (width, height)")

    model_config = makeSettingsConfigDict("SCRAPER__")

class ScraperImmobiliareIdSettings(ScraperSettings):
    """Settings for Immobiliare ID scraper."""

    # URL settings
    base_url: str = Field(default="https://www.immobiliare.it/", description="Base URL for Immobiliare scraper")
    use_sorting: bool = Field(default=True, description="Whether to use sorting in the scrape URL")
    sorting_url_param: str = Field(default="criterio=data&ordine=desc", description="URL parameter for sorting listings")
    use_filtering: bool = Field(default=True, description="Whether to apply filtering in the scrape URL")
    filter_url_param: str = Field(default="noAste=1", description="URL parameter for filtering listings") 

    # ID scraper specific settings
    max_pages: int = Field(default=80, description="Maximum number of pages to scrape")
    listing_limit: int = Field(default=2000, description="Maximum number of listings to scrape")

    model_config = makeSettingsConfigDict("SCRAPER__IMM_ID__")


class ScraperImmobiliareListingSettings(ScraperSettings):
    """Settings for Immobiliare listing details scraper."""

    # Override defaults for Immobiliare
    base_url: str = Field(default="https://www.immobiliare.it/", description="Base URL for Immobiliare scraper")
    url_prefix: str = Field(default="https://www.immobiliare.it/annunci/", description="Prefix for listing URLs")


    model_config = makeSettingsConfigDict("SCRAPER__IMM_LISTING__")
