"""
Data models for real estate properties.
"""
from pydantic import Field
from .base_model import BaseModelWithConfig

class RealEstate(BaseModelWithConfig):
    """Data model for a real estate property."""

    # Core identifiers
    id: str = Field(..., description="Unique identifier for the property")
    url: str = Field(..., description="URL of the property listing")
    contract: str = Field(..., description="Type of contract (sale, rent, etc.)")

    # Agency information
    agency_id: str | None = Field(None, description="Agency unique identifier")
    agency_url: str | None = Field(None, description="Agency website URL")
    agency_name: str | None = Field(None, description="Agency display name")
    is_private_ad: bool = Field(False, description="Whether this is a private listing")

    # Property status
    is_new: bool = Field(False, description="Whether the property is new construction")
    is_luxury: bool = Field(False, description="Whether this is a luxury property")

    # Pricing
    formatted_price: str = Field(..., description="Human-readable price string")
    price: int | None = Field(None, description="Numeric price value", ge=0)

    # Property details
    bathrooms: int | None = Field(None, description="Number of bathrooms", ge=0)
    bedrooms: int | None = Field(None, description="Number of bedrooms", ge=0)
    floor: str | None = Field(None, description="Floor designation")
    formatted_floor: str | None = Field(None, description="Human-readable floor info")
    total_floors: int | None = Field(None, description="Total floors in building", ge=0)
    condition: str | None = Field(None, description="Property condition")
    rooms: int | None = Field(None, description="Total number of rooms", ge=0)
    has_elevators: bool = Field(False, description="Whether building has elevators")

    # Surface area
    surface: float | None = Field(None, description="Property surface area in square meters", ge=0)
    surface_formatted: str | None = Field(None, description="Human-readable surface area")

    # Property classification
    type: str = Field(..., description="Property type (apartment, house, etc.)")
    caption: str | None = Field(None, description="Property caption/title")
    category: str = Field(..., description="Property category")
    description: str | None = Field(None, description="Property description")

    # Energy and utilities
    heating_type: str | None = Field(None, description="Type of heating system")
    air_conditioning: str | None = Field(None, description="Air conditioning type")

    # Location
    latitude: float = Field(..., description="Latitude coordinate", ge=-90, le=90)
    longitude: float = Field(..., description="Longitude coordinate", ge=-180, le=180)
    region: str = Field(..., description="Region/state")
    province: str = Field(..., description="Province")
    macrozone: str = Field(..., description="Macro geographical zone")
    microzone: str = Field(..., description="Micro geographical zone")
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country code")

    @classmethod
    def from_dict(cls, data: dict) -> "RealEstate":
        """Create a RealEstate instance from a dictionary."""
        # This is a more efficient way to validate and create the model using Pydantic.
        # This method will automatically validate the data and convert it
        # to the appropriate types as defined in the model.
        # If the model changes, this will ensure that the data is still valid.
        return RealEstate.model_validate(data)

    def to_dict(self) -> dict:
        """Convert the RealEstate instance to a dictionary."""
        return self.model_dump() 
