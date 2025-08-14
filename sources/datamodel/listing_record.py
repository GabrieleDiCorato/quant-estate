"""
Data model for real estate properties.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

import enumerations as enums
from pydantic import Field

from .base_datamodel import QuantEstateDataObject


class OtherFeatures(QuantEstateDataObject):
    """Data model for additional features of a property listing. Directly derived from the "other_features" field in ListingDetails."""

    has_built_in_wardrobe: bool | None = Field(None, description="Whether property has built-in wardrobe (Armadio a muro)")
    has_fireplace: bool | None = Field(None, description="Whether property has a fireplace (Caminetto)")
    has_tennis_court: bool | None = Field(None, description="Whether property has tennis court (Campo da tennis)")
    has_electric_gate: bool | None = Field(None, description="Whether property has electric gate (Cancello elettrico)")
    has_kitchen: bool | None = Field(None, description="Whether property has a kitchen (Cucina)")
    has_fiber_optic: bool | None = Field(None, description="Whether property has fiber optic connection (Fibra ottica)")
    has_private_or_shared_garden: bool | None = Field(None, description="Whether property has both private and shared garden")
    has_hot_tub: bool | None = Field(None, description="Whether property has hot tub/jacuzzi (Idromassaggio)")
    has_alarm_system: bool | None = Field(None, description="Whether property has alarm system (Impianto di allarme)")
    has_attic: bool | None = Field(None, description="Whether property has attic (Mansarda)")
    has_pool: bool | None = Field(None, description="Whether property has swimming pool (Piscina)")
    has_armored_door: bool | None = Field(None, description="Whether property has armored door (Porta blindata)")
    has_reception: bool | None = Field(None, description="Whether building has reception (Reception)")
    has_tavern: bool | None = Field(None, description="Whether property has tavern/basement room (Taverna)")
    has_video_intercom: bool | None = Field(None, description="Whether building has video intercom (VideoCitofono)")
    tv_system: enums.TvSystem | None = Field(None, description="TV system type")
    window_glass_type: enums.WindowGlassType | None = Field(None, description="Type of window glass")
    window_material: enums.WindowMaterial | None = Field(None, description="Window frame material")
    sun_exposure: str | None = Field(None, description="Sun exposure of the property (e.g., south, north, etc.)")


class ListingRecord(QuantEstateDataObject):
    """Data model for a real estate property. The normalized and cleaned version of ListingDetails."""
    
    # Core identifier
    id: str = Field(..., description="Unique QuantEstate identifier for the property listing")
    source: str = Field(..., description="Source of the listing data (e.g., IMMOBILIARE)")
    title: str = Field(..., description="Title of the property listing")
    url: str = Field(..., description="URL of the property listing")
    # Timestamps
    fetch_date: datetime = Field(default_factory=QuantEstateDataObject.get_timestamp, description="Timestamp of the last fetch of the listing details")
    last_updated: datetime | None = Field(None, description="Timestamp of the last update to the listing on the website (if provided)")
    etl_date: datetime = Field(default_factory=QuantEstateDataObject.get_timestamp, description="Creation timestamp of the record in the database")

    # Pricing
    # We only consider listings with transparent offer price (no price upon demand, no auction)
    price_eur: float = Field(..., description="Numeric price value in EUR", ge=0)
    maintenance_fee: float | None = Field(None, description="Monthly maintenance fee in EUR", ge=0)
    price_sqm: float | None = Field(None, description="Price per square meter in EUR", ge=0)

    # Property classification
    # From "type":
    property_type: enums.PropertyType = Field(
        ..., description="Specific property type (e.g., apartment, villa, etc.)"
    )
    ownership_type: enums.OwnershipType | None = Field(None, description="Type of ownership rights")
    property_class: enums.PropertyClass | None = Field(None, description="Property class based on quality and market positioning")
    # From "contract":
    contract_type: enums.ContractType = Field(
        ..., description="Type of contract (sale, rent, etc.)"
    )
    is_rent_to_own_available: bool = Field(False, description="Whether the property is available for rent-to-own") 
    current_availability: enums.CurrentAvailability | None = Field(
        None, description="Current availability status of the property"
    )
    # From "condition":
    condition: enums.PropertyCondition | None = Field(
        None, description="Property condition"
    )
    is_luxury: bool | None = Field(None, description="Whether this is a luxury property")

    # Property details
    surface: float = Field(..., description="Property surface area in square meters", ge=0)
    rooms: int | None = Field(None, description="Total number of rooms", ge=0)

    # Seminterrato, Rialzato, Terra, 1, 2, attico, mansarda, etc.
    floor: str | None = Field(None, description="Floor designation")
    total_floors: int | None = Field(None, description="Total floors in building", ge=0)

    # Composition
    bathrooms: int | None = Field(None, description="Number of bathrooms", ge=0)
    bedrooms: int | None = Field(None, description="Number of bedrooms", ge=0)
    has_balcony: bool | None = Field(None, description="Whether property has a balcony")
    has_terrace: bool | None = Field(None, description="Whether property has a terrace")
    has_elevator: bool | None = Field(None, description="Whether building has elevators")
    garden: enums.Garden | None = Field(
        None,
        description="Whether property has a garden, and its type (private, shared, etc.)",
    )
    has_cellar: bool | None = Field(None, description="Whether property has a cellar") # "Cantina"
    has_basement: bool | None = Field(None, description="Whether property has a basement")
    furnished: enums.FurnitureType | None = Field(
        None, description="Whether property is furnished"
    )
    kitchen: enums.KitchenType | None = Field(
        None, description="Type of kitchen (open, closed, etc.)"
    )

    # Building Info
    build_year: int | None = Field(None, description="Year the building was constructed", ge=1800, le=2100)
    has_concierge: bool | None = Field(None, description="Whether building has a concierge service")
    is_accessible: bool | None = Field(None, description="Whether the property is accessible for people with disabilities")

    # Energy and utilities
    heating_type: str | None = Field(None, description="Type of heating system")
    air_conditioning: str | None = Field(None, description="Air conditioning type")
    energy_class: enums.EnergyClass | None = Field(
        None, description="Energy efficiency class"
    )

    # Location
    country: str = Field(..., description="Country code")
    city: str = Field(..., description="City name")
    zone: str | None = Field(None, description="City zone or neighborhood")
    address: str | None = Field(None, description="Row address of the property")

    # Parking
    parking_info: str | None = Field(None, description="Parking information (garage, street parking, etc.)")

    # Extendend description
    description_title: str | None = Field(None, description="Title in the property description")
    description: str = Field(..., description="Property description")

    # From "other_amenities":
    other_features: OtherFeatures | None = Field(None, description="Additional features of the property")

    @classmethod
    def from_dict(cls, data: dict) -> "ListingRecord":
        """Create a RealEstate instance from a dictionary."""
        # This is a more efficient way to validate and create the model using Pydantic.
        # This method will automatically validate the data and convert it
        # to the appropriate types as defined in the model.
        # If the model changes, this will ensure that the data is still valid.
        return ListingRecord.model_validate(data)

    def to_dict(self) -> dict:
        """Convert the RealEstate instance to a dictionary."""
        return self.model_dump() 
