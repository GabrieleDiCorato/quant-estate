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
from collections.abc import Mapping
from zoneinfo import ZoneInfo

from sources.datamodel import ListingDetails
from sources.datamodel import ListingRecord, OtherFeatures
import sources.datamodel.enumerations as enums
# Use Italian -> Enum mappings from Immobiliare mapper
from sources.mappers import (
    IMM_PROPERTY_CONDITION_MAP as COND_MAP,
    IMM_CONTRACT_TYPE_MAP as CONTRACT_MAP,
    IMM_FURNITURE_MAP as FURNITURE_MAP,
    IMM_GARDEN_MAP as GARDEN_MAP,
    IMM_KITCHEN_MAP as KITCHEN_MAP,
    IMM_OWNERSHIP_MAP as OWNERSHIP_MAP,
    IMM_PROPERTY_CLASS_MAP as CLASS_MAP,
    IMM_PROPERTY_TYPE_MAP as TYPE_MAP,
    IMM_TV_SYSTEM_MAP as TV_MAP,
    IMM_WINDOW_GLASS_MAP as GLASS_MAP,
    IMM_WINDOW_MATERIAL_MAP as WINDOW_MATERIAL_MAP,
    IMM_OTHER_FEATURES as OTHER_FEATURES
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ListingDataTransformer:
    """Transforms ListingDetails CSV data to ListingRecord instances."""

    def __init__(self):
        pass

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
        contract_type, rent_to_own, available = self._parse_contract_field(listing.contract)

        # Extract amenities
        other_features = self._map_other_features(listing.other_features or [])

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
            # From "type"
            property_type=property_type,
            ownership_type=ownership,
            property_class=property_class,
            # From "contract"
            contract_type=contract_type,
            is_rent_to_own_available=rent_to_own,
            current_availability=available,
            is_luxury=listing.is_luxury == "true" if listing.is_luxury else None,
            # Property condition
            condition=self._parse_enumeration_field(
                "condition", listing.condition or "", COND_MAP
            ),
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
                self._parse_enumeration_field("garden", listing.garden, GARDEN_MAP)
                if isinstance(listing.garden, str)
                else None
            ),
            has_cellar=listing.cellar,
            has_basement=None,
            furnished=self._parse_enumeration_field(
                "furnished", listing.furnished or "", FURNITURE_MAP
            ),
            kitchen=self._parse_enumeration_field(
                "kitchen", listing.kitchen or "", KITCHEN_MAP
            ),
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
            other_features=other_features,
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

        property_type: enums.PropertyType | None = self._parse_enumeration_field("property_type", parts[0], TYPE_MAP)
        if not property_type:
            raise ValueError(f"Unknown property type in field 'type': [{parts[0]}]")

        if len(parts) == 1:
            return property_type, None, None
        elif len(parts) == 2:
            second_part = parts[1]
            # Try to parse second part as ownership type first
            ownership_type = self._parse_enumeration_field("ownership_type", second_part, OWNERSHIP_MAP)

            # If second part is not an ownership type, try as property class
            if ownership_type is None:
                property_class = self._parse_enumeration_field("property_class", second_part, CLASS_MAP)
                return property_type, ownership_type, property_class
            else:
                logger.warning("Failed to parse string '%s' as either ownership type or property class", second_part)
                return property_type, ownership_type, None
        else:
            if len(parts) > 3:
                logger.warning("Unexpected number of parts in 'type' field: %s", parts)

            # Second part is always ownership type
            ownership_type = self._parse_enumeration_field("ownership_type", parts[1], OWNERSHIP_MAP)
            # Third part is always property class
            property_class = self._parse_enumeration_field("property_class", parts[2], CLASS_MAP)

            return property_type, ownership_type, property_class

    @staticmethod
    def _parse_enumeration_field[T: enums.BaseEnum](
        field_name: str,
        field_value_str: str,
        mapping: Mapping[str, T],
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

    def _parse_contract_field(
            self,
            contract_field: str
    ) -> tuple[enums.ContractType, bool, enums.CurrentAvailability | None]:
        """Parse the 'contract' field.
        This field is a pipe-separated string with various, unsorted, information.
        """
        if not contract_field or not contract_field.strip():
            raise ValueError("Field 'contract' is empty or missing")

        contract_str = contract_field.strip()

        # Match contract type
        contract_type: enums.ContractType | None = None
        for key, value in CONTRACT_MAP.items():
            if key in contract_str:
                contract_type = value
                break

        if contract_type is None:
            raise ValueError(f"Unknown contract type: [{contract_field}]")

        is_rent_to_own_available: bool = self._is_rent_to_own_available(contract_field)
        is_currently_available: enums.CurrentAvailability | None = self._is_currently_available(contract_field)
        return contract_type, is_rent_to_own_available, is_currently_available

    def _is_rent_to_own_available(self, contract_field: str) -> bool:
        """Check if rent-to-own is available based on the contract field."""
        if not contract_field or not contract_field.strip():
            return False
        return "riscatto" in contract_field

    def _is_currently_available(self, contract_field: str) -> enums.CurrentAvailability | None:
        """Check the current availability based on the contract field."""
        if not contract_field or not contract_field.strip():
            return None
        contract_field = contract_field.strip().lower()
        if "libero" in contract_field:
            return enums.CurrentAvailability.AVAILABLE
        elif "a reddito" in contract_field:
            return enums.CurrentAvailability.OCCUPIED
        return None

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

        amenities: dict[str, Any] = {}
        # Process other_amenities columns
        for amenity_value_raw in features:
            amenity_value = amenity_value_raw.strip()
            if not amenity_value:
                continue
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
        for glass_text, glass_enum in GLASS_MAP.items():
            if glass_text in amenity_lower:
                amenities["window_glass_type"] = glass_enum
                break

        # Check for window materials
        for material_text, material_enum in WINDOW_MATERIAL_MAP.items():
            if material_text.lower() in amenity_lower:
                amenities["window_material"] = material_enum
                break

        # Check for TV system
        for tv_text, tv_enum in TV_MAP.items():
            if tv_text in amenity_value:
                amenities["tv_system"] = tv_enum
                break

        # Check for exposure information
        if "esposizione" in amenity_lower:
            amenities["sun_exposure"] = amenity_value

    def _extract_window_info(self, row: Dict[str, str]) -> dict[str, Any]:
        """Extract window glass type and material from amenity fields."""
        window_info: dict[str, Any] = {}

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
