#!/usr/bin/env python3
"""
ETL Pipeline Prototype: ListingDetails to ListingRecord Mapping

This script demonstrates how to transform ListingDetails instances from CSV data
into normalized ListingRecord instances, handling data parsing, type conversion,
and enumeration mapping.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from sources.datamodel.listing_details import ListingDetails
from sources.datamodel.listing_record import ListingRecord, OtherFeatures
import sources.datamodel.enumerations as enums
from sources.mappers.immobiliare_enum_mapper import (
    IMM_PROPERTY_CONDITION_MAP,
    IMM_CONTRACT_TYPE_MAP,
    IMM_ENERGY_CLASS_MAP,
    IMM_FURNITURE_MAP,
    IMM_GARDEN_MAP,
    IMM_KITCHEN_MAP,
    IMM_OWNERSHIP_MAP,
    IMM_PROPERTY_CLASS_MAP,
    IMM_PROPERTY_TYPE_MAP,
    IMM_TV_SYSTEM_MAP,
    IMM_WINDOW_GLASS_MAP,
    IMM_WINDOW_MATERIAL_MAP,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ListingDataTransformer:
    """Transforms ListingDetails CSV data to ListingRecord instances."""

    def __init__(self):
        """Initialize the transformer with mapping dictionaries."""
        # Use Italian -> Enum mappings from Immobiliare mapper
        self.condition_mapping: dict[str, enums.PropertyCondition] = IMM_PROPERTY_CONDITION_MAP
        self.contract_type_mapping: dict[str, enums.ContractType] = IMM_CONTRACT_TYPE_MAP
        self.energy_class_mapping: dict[str, enums.EnergyClass] = IMM_ENERGY_CLASS_MAP
        self.furniture_mapping: dict[str, enums.FurnitureType] = IMM_FURNITURE_MAP
        self.garden_mapping: dict[str, enums.Garden] = IMM_GARDEN_MAP
        self.kitchen_mapping: dict[str, enums.KitchenType] = IMM_KITCHEN_MAP
        self.ownership_type_mapping: dict[str, enums.OwnershipType] = IMM_OWNERSHIP_MAP
        self.property_class_mapping: dict[str, enums.PropertyClass] = IMM_PROPERTY_CLASS_MAP
        self.property_type_mapping: dict[str, enums.PropertyType] = IMM_PROPERTY_TYPE_MAP
        self.tv_system_mapping: dict[str, enums.TvSystem] = IMM_TV_SYSTEM_MAP
        self.window_glass_mapping: dict[str, enums.WindowGlassType] = IMM_WINDOW_GLASS_MAP
        self.window_material_mapping: dict[str, enums.WindowMaterial] = IMM_WINDOW_MATERIAL_MAP

        # Only keep custom mappings for amenities since they map to boolean fields
        self.amenity_mapping: dict[str, str] = {
            "Armadio a muro": "has_built_in_wardrobe",
            "Caminetto": "has_fireplace",
            "Campo da tennis": "has_tennis_court",
            "Cancello elettrico": "has_electric_gate",
            "Cucina": "has_kitchen",
            "Fibra ottica": "has_fiber_optic",
            "Giardino privato e comune": "has_private_or_shared_garden",
            "Idromassaggio": "has_hot_tub",
            "Impianto di allarme": "has_alarm_system",
            "Mansarda": "has_attic",
            "Piscina": "has_pool",
            "Porta blindata": "has_armored_door",
            "Reception": "has_reception",
            "Taverna": "has_tavern",
            "VideoCitofono": "has_video_intercom",
        }

    @staticmethod
    def _reverse_enum_mapping[E: enums.BaseEnum](enum_mapping: type[E]) -> dict[str, E]:
        """Reverse the enum mapping to get a dictionary of value to enum."""
        return {enum.value: enum for enum in enum_mapping}

    def map(self, listing: ListingDetails) -> ListingRecord:
        try:
            return self._map(listing)
        except Exception as e:
            logger.error("Error mapping listing [%s]: %s", listing.id, e)
            raise ValueError(f"Failed to map listing {listing.id}: {e}") from e

    def _map(self, listing: ListingDetails) -> ListingRecord:
        """Transform a single ListingDetails instance to a ListingRecord instance."""
        # Parse composite fields
        property_type, ownership, property_class = self._parse_type_field(listing.type)
        contract_info = self._parse_contract_field(listing.contract)

        # Extract amenities
        amenities = self._map_other_features(listing.other_features or [])

        return ListingRecord(
            # Core identifier
            id=listing.id,
            source=listing.source,
            title=listing.title,
            url=listing.url,
            # Timestamps
            fetch_date=listing.fetch_date,
            last_updated=listing.last_updated,
            etl_date=datetime.now(tz=ZoneInfo("Europe/Rome")),
            # Pricing
            price_eur=listing.price_eur,
            maintenance_fee=listing.maintenance_fee,
            price_sqm=listing.price_sqm,
            # Property classification from parsed fields
            property_type=property_type,
            ownership_type=ownership,
            property_class=property_class,
            contract_type=contract_info["contract_type"],
            is_rent_to_own_available=False,
            current_availability=enums.CurrentAvailability.AVAILABLE,
            is_luxury=listing.is_luxury == "true" if listing.is_luxury else None,
            # Property condition
            condition=self._parse_enumeration_field("condition", listing.condition or "", self.condition_mapping),
            # Property details
            surface=self._require_float(listing.surface, "surface"),
            rooms=listing.rooms,
            floor=listing.floor,
            total_floors=listing.total_floors,
            bathrooms=listing.bathrooms,
            bedrooms=listing.bedrooms,
            has_balcony=listing.balcony,
            has_terrace=listing.terrace,
            has_elevator=listing.elevator,
            garden=(
                self._parse_enumeration_field("garden", listing.garden, self.garden_mapping)
                if isinstance(listing.garden, str) else None
            ),
            has_cellar=listing.cellar,
            has_basement=None,
            furnished=self._parse_enumeration_field("furnished", listing.furnished or "", self.furniture_mapping),
            kitchen=self._parse_enumeration_field("kitchen", listing.kitchen or "", self.kitchen_mapping),
            # Building info
            build_year=listing.build_year,
            has_concierge=listing.concierge,
            is_accessible=listing.is_accessible,
            # Energy and utilities
            heating_type=listing.heating_type,
            air_conditioning=listing.air_conditioning,
            energy_class=listing.energy_class,
            # Location
            country=listing.country or "IT",
            city=listing.city,
            zone=self._extract_zone_from_address(listing.address),
            address=listing.address,
            # Parking
            parking_info=None,
            # Description
            description_title=listing.description_title,
            description=listing.description,
            other_features=amenities,
        )

    def _parse_composite_field(self, field_value: str, separator: str = " | ") -> List[str]:
        """Parse composite fields that contain multiple values separated by delimiters."""
        if not field_value or field_value.strip() == "":
            return []
        return [part.strip() for part in field_value.split(separator) if part.strip()]

    def _require_float(self, value: Optional[float], field_name: str) -> float:
        """Ensure a float value is present; raise if missing."""
        if value is None:
            raise ValueError(f"Missing required field '{field_name}'")
        return float(value)

    def _parse_type_field(
        self, type_field: str
    ) -> tuple[enums.PropertyType, enums.OwnershipType | None, enums.PropertyClass | None]:
        """Parse the 'type' field which contains property type, ownership, and class info."""
        parts = self._parse_composite_field(type_field, separator="|")

        # The first part is always the property type
        if not parts or len(parts) == 0:
            raise ValueError(f"Field 'type' is empty or invalid: [{type_field}]")

        property_type: enums.PropertyType | None = self._parse_enumeration_field("property_type", parts[0], self.property_type_mapping)
        if not property_type:
            raise ValueError(f"Unknown property type in field 'type': [{parts[0]}]")

        if len(parts) == 1:
            return property_type, None, None
        elif len(parts) == 2:
            second_part = parts[1]
            # Try to parse second part as ownership type first
            ownership_type = self._parse_enumeration_field("ownership_type", second_part, self.ownership_type_mapping)

            # If second part is not an ownership type, try as property class
            if ownership_type is None:
                property_class = self._parse_enumeration_field("property_class", second_part, self.property_class_mapping)
                return property_type, ownership_type, property_class
            else:
                logger.warning("Failed to parse string '%s' as either ownership type or property class", second_part)
                return property_type, ownership_type, None
        else:   
            if len(parts) > 3:
                logger.warning("Unexpected number of parts in 'type' field: %s", parts)

            # Second part is always ownership type
            ownership_type = self._parse_enumeration_field("ownership_type", parts[1], self.ownership_type_mapping)
            # Third part is always property class
            property_class = self._parse_enumeration_field("property_class", parts[2], self.property_class_mapping)

            return property_type, ownership_type, property_class

    @staticmethod
    def _parse_enumeration_field[T: enums.BaseEnum](
            field_name: str,
            field_value_str: str,
            mapping: dict[str, T]
    ) -> T | None:
        """Parse a field that maps to an enumeration."""
        if not field_value_str or str(field_value_str).strip() == "":
            return None
        raw = str(field_value_str).strip()
        # Exact match first
        parsed_value = mapping.get(raw)
        if parsed_value is not None:
            return parsed_value
        # Case-insensitive fallback
        raw_lower = raw.lower()
        for k, v in mapping.items():
            if k.lower() == raw_lower:
                return v
        logger.warning("Unknown value '%s' for field '%s'", field_value_str, field_name)
        return None

    def _parse_contract_field(self, contract_field: str) -> Dict[str, Any]:
        """Parse the 'contract' field."""
        if not contract_field:
            raise ValueError("Field 'contract' is empty or missing")

        label = contract_field.strip()
        # Try exact first (e.g., 'Vendita'), then lowercase mapping fallback
        value = self.contract_type_mapping.get(label)
        if value is None:
            value = self.contract_type_mapping.get(label.lower())

        if value is None:
            raise ValueError(f"Unknown contract type: [{contract_field}]")

        return {"contract_type": value}

    def _safe_bool_conversion(self, value: Optional[str]) -> Optional[bool]:
        """Safely convert string values to boolean."""
        if not value or value.strip() == "":
            return None
        value_lower = value.lower().strip()
        if value_lower in ["true", "sì", "si", "yes", "1"]:
            return True
        elif value_lower in ["false", "no", "0"]:
            return False
        return None

    def _safe_int_conversion(self, value: Optional[str]) -> Optional[int]:
        """Safely convert string values to integer."""
        if not value or value.strip() == "":
            return None
        try:
            return int(float(value))  # Handle cases where value might be "1.0"
        except (ValueError, TypeError):
            return None

    def _safe_float_conversion(self, value: Optional[str]) -> Optional[float]:
        """Safely convert string values to float."""
        if not value or value.strip() == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not date_str or date_str.strip() == "":
            return None
        try:
            # Handle ISO format with Z suffix
            if date_str.endswith('Z'):
                date_str = date_str.replace('Z', '+00:00')
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse datetime: {date_str}")
            return None

    def _extract_zone_from_address(self, address: Optional[str]) -> Optional[str]:
        """Extract zone/neighborhood from address string."""
        if not address:
            return None

        # Look for patterns like "Milano/Zone/Street"
        parts = address.split('/')
        if len(parts) >= 2:
            return parts[1]  # Return the zone part
        return None

    def _map_other_features(self, features: list[str]) -> OtherFeatures | None:
        """Extract amenities from other_amenities columns and additional fields."""

        if not features or len(features) <= 0:
            return None

        amenities = {}
        # Process other_amenities columns
        for i in range(len(features)):
            amenity_value = features[i].strip()
            if amenity_value:
                # Direct amenity mapping
                if amenity_value in self.amenity_mapping:
                    field_name = self.amenity_mapping[amenity_value]
                    amenities[field_name] = True

                # Handle composite amenity descriptions like "Infissi esterni in doppio vetro / PVC"
                self._parse_composite_amenity(amenity_value, amenities)

        if not amenities:
            return None
        return OtherFeatures(**amenities)

    def _parse_composite_amenity(self, amenity_value: str, amenities: Dict[str, Any]) -> None:
        """Parse composite amenity descriptions for window types and materials."""
        amenity_lower = amenity_value.lower()

        # Check for window glass types
        for glass_text, glass_enum in self.window_glass_mapping.items():
            if glass_text in amenity_lower:
                amenities["window_glass_type"] = glass_enum
                break

        # Check for window materials
        for material_text, material_enum in self.window_material_mapping.items():
            if material_text.lower() in amenity_lower:
                amenities["window_material"] = material_enum
                break

        # Check for TV system
        for tv_text, tv_enum in self.tv_system_mapping.items():
            if tv_text in amenity_value:
                amenities["tv_system"] = tv_enum
                break

        # Check for exposure information
        if "esposizione" in amenity_lower:
            amenities["sun_exposure"] = amenity_value

    def _extract_window_info(self, row: Dict[str, str]) -> dict[str, Any]:
        """Extract window glass type and material from amenity fields."""
        window_info = {}

        # Look through all other_amenities columns for window information
        for i in range(8):
            amenity_key = f"other_amenities[{i}]"
            if amenity_key in row and row[amenity_key]:
                amenity_value = row[amenity_key].lower()

                # Extract window glass type
                if "doppio vetro" in amenity_value:
                    window_info["window_glass_type"] = enums.WindowGlassType.DOUBLE_GLASS
                elif "triplo vetro" in amenity_value:
                    window_info["window_glass_type"] = enums.WindowGlassType.TRIPLE_GLASS
                elif "vetro" in amenity_value and "doppio" not in amenity_value:
                    window_info["window_glass_type"] = enums.WindowGlassType.SINGLE_GLASS

                # Extract window material
                if "pvc" in amenity_value:
                    window_info["window_material"] = enums.WindowMaterial.PVC
                elif "legno" in amenity_value:
                    window_info["window_material"] = enums.WindowMaterial.WOOD
                elif "metallo" in amenity_value:
                    window_info["window_material"] = enums.WindowMaterial.METAL

        return window_info
