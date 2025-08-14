"""
Data model for real estate properties.
"""

from datetime import datetime

from pydantic import Field

from .base_datamodel import QuantEstateDataObject
from .enumerations import EnergyClass


class ListingDetails(QuantEstateDataObject):
    """Data model for a real estate property."""

    # Core identifier
    id: str = Field(..., description="Unique QuantEstate identifier for the property listing")
    source: str = Field(..., description="Source of the listing data (e.g., IMMOBILIARE)")
    title: str = Field(..., description="Title of the property listing")
    url: str = Field(..., description="URL of the property listing")
    # Timestamps
    fetch_date: datetime = Field(
        default_factory=QuantEstateDataObject.get_timestamp,
        description="Timestamp of the last fetch of the listing details",
    )
    last_updated: datetime | None = Field(
        None, description="Timestamp of the last update to the listing on the website (if provided)"
    )

    # Pricing
    # We only consider listings with transparent offer price (no price upon demand, no auction)
    formatted_price: str = Field(..., description="Human-readable price string")
    price_eur: float = Field(..., description="Numeric price value in EUR", ge=0)
    formatted_maintenance_fee: str | None = Field(
        None, description="Human-readable maintenance fee string"
    )
    maintenance_fee: float | None = Field(None, description="Monthly maintenance fee in EUR", ge=0)
    formatted_price_sqm: str | None = Field(
        None, description="Human-readable price per square meter string"
    )
    price_sqm: float | None = Field(None, description="Price per square meter in EUR", ge=0)

    # Property classification
    type: str = Field(..., description="Property type (apartment, house, etc.)", min_length=1)
    contract: str = Field(..., description="Type of contract (sale, rent, etc.)")
    condition: str | None = Field(None, description="Property condition (renovated, new, etc.)")
    # Derived field (from the "Condition" field)
    # is_new: bool | None = Field(None, description="Whether the property is new construction")
    is_luxury: bool | None = Field(None, description="Whether this is a luxury property")

    # Property details
    surface_formatted: str = Field(..., description="Human-readable surface area")
    surface: float | None = Field(None, description="Property surface area in square meters", ge=0)
    rooms: int | None = Field(None, description="Total number of rooms", ge=0)
    # Seminterrato, Rialzato, Terra, 1, 2, attico, mansarda, etc.
    floor: str | None = Field(None, description="Floor designation")
    total_floors: int | None = Field(None, description="Total floors in building", ge=0)

    # Composition
    bathrooms: int | None = Field(None, description="Number of bathrooms", ge=0)
    bedrooms: int | None = Field(None, description="Number of bedrooms", ge=0)
    balcony: bool | None = Field(None, description="Whether property has a balcony")
    terrace: bool | None = Field(None, description="Whether property has a terrace")
    elevator: bool | None = Field(None, description="Whether building has elevators")
    garden: str | None = Field(
        None, description="Whether property has a garden, and its type (private, shared, etc.)"
    )
    cellar: bool | None = Field(None, description="Whether property has a cellar")  # "Cantina"
    basement: bool | None = Field(None, description="Whether property has a basement")
    furnished: str | None = Field(None, description="Whether property is furnished")
    kitchen: str | None = Field(None, description="Type of kitchen (open, closed, etc.)")

    # Building Info
    build_year: int | None = Field(
        None, description="Year the building was constructed", ge=1800, le=2100
    )
    concierge: bool | None = Field(None, description="Whether building has a concierge service")
    is_accessible: bool | None = Field(
        None, description="Whether the property is accessible for people with disabilities"
    )

    # Energy and utilities
    heating_type: str | None = Field(None, description="Type of heating system")
    air_conditioning: str | None = Field(None, description="Air conditioning type")
    energy_class: EnergyClass | None = Field(None, description="Energy efficiency class")

    # Location
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country code")
    address: str | None = Field(None, description="Full address of the property")

    # Parking
    parking_info: str | None = Field(
        None, description="Parking information (garage, street parking, etc.)"
    )

    # Extendend description
    description_title: str | None = Field(None, description="Title in the property description")
    description: str = Field(..., description="Property description")
    other_amenities: list[str] | None = Field(
        None, description="List of other amenities or features"
    )

    @classmethod
    def from_dict(cls, data: dict) -> "ListingDetails":
        """Create a RealEstate instance from a dictionary."""
        # This is a more efficient way to validate and create the model using Pydantic.
        # This method will automatically validate the data and convert it
        # to the appropriate types as defined in the model.
        # If the model changes, this will ensure that the data is still valid.
        data.pop('_id', None)
        return ListingDetails.model_validate(data)

    def to_dict(self) -> dict:
        """Convert the RealEstate instance to a dictionary."""
        return self.model_dump()
