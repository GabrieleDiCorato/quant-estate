"""
Data models for real estate properties.
"""
from pydantic import Field, HttpUrl
from .base_model import BaseModelWithConfig
from .enumerations import *

class RealEstateListing(BaseModelWithConfig):
    """Data model for a real estate property."""

    # Core identifiers
    id: str = Field(..., description="Unique identifier for the property")
    title: str = Field(..., description="Title of the property listing")
    url: HttpUrl = Field(..., description="URL of the property listing") # http or https, TLD required, host required, max length 2083.

    # Pricing
    formatted_price: str = Field(..., description="Human-readable price string")
    price_eur: float = Field(..., description="Numeric price value in EUR", ge=0)
    formatted_maintenance_fee: str | None = Field(None, description="Human-readable maintenance fee string")
    maintenance_fee: float | None = Field(None, description="Monthly maintenance fee in EUR", ge=0)

    # Property classification
    type: PropertyType = Field(..., description="Property type (apartment, house, etc.)")
    contract: ContractType = Field(..., description="Type of contract (sale, rent, etc.)")
    condition: ConditionType | None = Field(None, description="Property condition (renovated, new, etc.)")
    is_new: bool | None = Field(None, description="Whether the property is new construction")
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
    garden: bool | None = Field(None, description="Whether property has a garden")
    cellar: bool | None = Field(None, description="Whether property has a cellar") # "Cantina"
    basement: bool | None = Field(None, description="Whether property has a basement")
    furnished: bool | None = Field(None, description="Whether property is furnished")

    # Building Info
    build_year: int | None = Field(None, description="Year the building was constructed", ge=1800, le=2100)
    considerge: bool | None = Field(None, description="Whether building has a concierge service")
    is_accessible: bool | None = Field(None, description="Whether the property is accessible for people with disabilities")

    # Extedend description
    description: str = Field(..., description="Property description")
    other_amenities: list[str] | None = Field(None, description="List of other amenities or features")

    # Energy and utilities
    heating_type: HeatingType | None = Field(None, description="Type of heating system")
    air_conditioning: AirConditioningType | None = Field(None, description="Air conditioning type")
    energy_class: EnergyClass | None = Field(None, description="Energy efficiency class")

    # Location
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country code")
    address: str | None = Field(None, description="Full address of the property")

    # Parking
    parking_info: str | None = Field(None, description="Parking information (garage, street parking, etc.)")

    @classmethod
    def from_dict(cls, data: dict) -> "RealEstateListing":
        """Create a RealEstate instance from a dictionary."""
        # This is a more efficient way to validate and create the model using Pydantic.
        # This method will automatically validate the data and convert it
        # to the appropriate types as defined in the model.
        # If the model changes, this will ensure that the data is still valid.
        return RealEstateListing.model_validate(data)

    def to_dict(self) -> dict:
        """Convert the RealEstate instance to a dictionary."""
        return self.model_dump() 
