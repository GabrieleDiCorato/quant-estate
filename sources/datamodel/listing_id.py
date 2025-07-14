from pydantic import Field, HttpUrl, computed_field
from .base_datamodel import QuantEstateDataObject
from .enumerations import Source
from functools import cached_property

class ListingId(QuantEstateDataObject):
    """Data model for a real estate property listing identifier."""

    # Core identifiers
    source: Source = Field(..., description="Source of the listing data (e.g., IMMOBILIARE)")
    source_id: str = Field(..., description="Identifier for the property in the source system")
    title: str = Field(..., description="Title of the property listing")
    url: HttpUrl = Field(..., description="URL of the property listing") # http or https, TLD required, host required, max length 2083.

    @computed_field(description="Unique QuantEstate identifier for the listing")
    @cached_property
    def id(self) -> str:
        """Generate a unique identifier for the listing based on source and source_id."""
        return f"{self.source.value}:{self.source_id}"
