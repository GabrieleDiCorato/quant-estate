from datetime import datetime
from functools import cached_property
from zoneinfo import ZoneInfo

from pydantic import Field, computed_field

from .base_datamodel import QuantEstateDataObject


class ListingId(QuantEstateDataObject):
    """Data model for a real estate property listing identifier."""

    # Core identifiers
    source: str = Field(..., description="Source of the listing data (e.g., IMMOBILIARE)")
    source_id: str = Field(..., description="Identifier for the property in the source system")
    title: str = Field(..., description="Title of the property listing")
    url: str = Field(..., description="URL of the property listing")
    fetch_date: datetime | None = Field(
        datetime.now(tz=ZoneInfo("Europe/Rome")),
        description="Timestamp of the last fetch of the listing details",
    )  # Optional for backward compatibility

    @computed_field(description="Unique QuantEstate identifier for the listing")
    @cached_property
    def id(self) -> str:
        """Generate a unique identifier for the listing based on source and source_id."""
        return f"{self.source}:{self.source_id}"

    @classmethod
    def from_dict(cls, data: dict) -> "ListingId":
        """Create a ListingId instance from a dictionary."""
        data.pop('_id', None)
        data.pop('id', None)
        return ListingId.model_validate(data)
