#!/usr/bin/env python3
"""
ETL Pipeline Prototype: ListingDetails to ListingRecord Mapping

This script demonstrates how to transform ListingDetails instances from CSV data
into normalized ListingRecord instances, handling data parsing, type conversion,
and enumeration mapping.
"""

import logging
import re
from collections.abc import Mapping
from datetime import datetime
from zoneinfo import ZoneInfo

import sources.datamodel.enumerations as enums
from sources.datamodel import ListingDetails, ListingRecord, OtherFeatures
from sources.mappers import IMM_CONTRACT_TYPE_MAP as CONTRACT_MAP
from sources.mappers import IMM_FURNITURE_MAP as FURNITURE_MAP
from sources.mappers import IMM_GARDEN_MAP as GARDEN_MAP
from sources.mappers import IMM_KITCHEN_MAP as KITCHEN_MAP
from sources.mappers import IMM_OTHER_FEATURES as OTHER_FEATURES
from sources.mappers import IMM_OWNERSHIP_MAP as OWNERSHIP_MAP
from sources.mappers import IMM_PROPERTY_CLASS_MAP as CLASS_MAP

# Use Italian -> Enum mappings from Immobiliare mapper
from sources.mappers import IMM_PROPERTY_CONDITION_MAP as COND_MAP
from sources.mappers import IMM_PROPERTY_TYPE_MAP as TYPE_MAP
from sources.mappers import IMM_TV_SYSTEM_MAP as TV_MAP
from sources.mappers import IMM_WINDOW_MATERIAL_MAP as WINDOW_MATERIAL_MAP

logger = logging.getLogger(__name__)


class ListingDataTransformer:
    """Transforms ListingDetails CSV data to ListingRecord instances."""

    def map(self, listing: ListingDetails) -> ListingRecord:
        """Transform a single ListingDetails instance to a ListingRecord instance."""
        # Parse composite fields
        property_type, ownership, property_class = self._parse_type_field(listing.type)
        contract_type, rent_to_own, available = self._parse_contract_field(listing.contract)
        condition: enums.PropertyCondition | None = (
            self._parse_enumeration_field("condition", listing.condition, COND_MAP)
            if listing.condition
            else None
        )
        surface: float = self._parse_surface(listing.surface_formatted)
        garden: enums.Garden | None = self._parse_garden(listing.garden)
        furnished: enums.FurnitureType | None = (
            self._parse_enumeration_field("furnished", listing.furnished, FURNITURE_MAP)
            if listing.furnished
            else None
        )
        kitchen: enums.KitchenType | None = (
            self._parse_enumeration_field("kitchen", listing.kitchen, KITCHEN_MAP)
            if listing.kitchen
            else None
        )
        zone, address = self._parse_address(listing.address) if listing.address else (None, None)
        other_features = self._map_other_features(listing.other_amenities) if listing.other_amenities else None

        # Create and validate the ListingRecord using Pydantic validations
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
            # From "condition"
            condition=condition,
            is_luxury=listing.is_luxury,
            # Property details
            surface=surface,
            rooms=listing.rooms,
            floor=listing.floor,
            total_floors=listing.total_floors,
            bathrooms=listing.bathrooms,
            bedrooms=listing.bedrooms,
            has_balcony=listing.balcony,
            has_terrace=listing.terrace,
            has_elevator=listing.elevator,
            garden=garden,
            has_cellar=listing.cellar,
            has_basement=None,
            furnished=furnished,
            kitchen=kitchen,
            # Building info
            build_year=listing.build_year,
            has_concierge=listing.concierge,
            is_accessible=listing.is_accessible,
            # Energy and utilities
            heating_type=listing.heating_type,
            air_conditioning=listing.air_conditioning,
            energy_class=listing.energy_class,
            # Location
            country=listing.country,
            city=listing.city,
            zone=zone,
            address=address,
            # Parking
            parking_info=listing.parking_info,
            # Description
            description_title=listing.description_title,
            description=listing.description,
            other_features=other_features,
        )

    def _parse_composite_field(self, field_value: str, separator: str = " | ") -> list[str]:
        """Parse composite fields that contain multiple values separated by delimiters."""
        if not field_value or field_value.strip() == "":
            return []
        return [part.strip() for part in field_value.split(separator) if part.strip()]

    def _parse_type_field(
        self, type_field: str
    ) -> tuple[enums.PropertyType, enums.OwnershipType | None, enums.PropertyClass | None]:
        """Parse the 'type' field which contains property type, ownership, and class info."""
        logger.debug("Parsing 'type' field: %s", type_field)
        parts = self._parse_composite_field(type_field, separator="|")

        # The first part is always the property type
        if not parts or len(parts) == 0:
            raise ValueError(f"Field 'type' is empty or invalid: [{type_field}]")

        property_type: enums.PropertyType | None = self._parse_enumeration_field(
            "property_type", parts[0], TYPE_MAP
        )
        if not property_type:
            raise ValueError(f"Unknown property type in field 'type': [{parts[0]}]")

        if len(parts) == 1:
            return property_type, None, None
        elif len(parts) == 2:
            second_part = parts[1]
            # Try to parse second part as ownership type first. The parse is not strict since it's an attempt
            ownership_type = self._parse_enumeration_field(
                "ownership_type", second_part, OWNERSHIP_MAP, strict=False
            )

            # If second part is not an ownership type, try as property class
            if ownership_type is not None:
                return property_type, ownership_type, None
            else:
                property_class = self._parse_enumeration_field(
                    "property_class", second_part, CLASS_MAP
                )
                if property_class is None:
                    logger.warning("Failed to parse string [%s] as either ownership type or property class", second_part)
                
                return property_type, None, property_class
        else:
            if len(parts) > 3:
                logger.warning("Unexpected number of parts in 'type' field: %s", parts)

            # Second part is always ownership type
            ownership_type = self._parse_enumeration_field(
                "ownership_type", parts[1], OWNERSHIP_MAP
            )
            # Third part is always property class
            property_class = self._parse_enumeration_field("property_class", parts[2], CLASS_MAP)

            return property_type, ownership_type, property_class

    @staticmethod
    def _parse_enumeration_field[T: enums.BaseEnum](
        field_name: str,
        field_value_str: str,
        mapping: Mapping[str, T],
        strict=True
    ) -> T | None:
        """Parse a field that maps to an enumeration."""
        if not field_value_str or str(field_value_str).strip() == "":
            return None
        # Normalize once
        raw_str = str(field_value_str).strip()
        # Exact match first
        parsed_value = mapping.get(raw_str)
        if parsed_value is not None:
            return parsed_value
        # Case-insensitive fallback
        if not strict:
            raw_lower = raw_str.lower()
            for k, v in mapping.items():
                if k.lower() == raw_lower:
                    return v
        if strict:
            logger.warning("Unknown value '%s' for field '%s'", field_value_str, field_name)
        return None

    def _parse_contract_field(
        self, contract_field: str
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

        is_rent_to_own_available: bool = self._is_rent_to_own_available(contract_str)
        is_currently_available: enums.CurrentAvailability | None = self._is_currently_available(
            contract_str
        )
        return contract_type, is_rent_to_own_available, is_currently_available

    def _is_rent_to_own_available(self, contract_field: str) -> bool:
        """Check if rent-to-own is available based on the contract field."""
        return "riscatto" in contract_field.lower()

    def _is_currently_available(self, contract_field: str) -> enums.CurrentAvailability | None:
        """Check the current availability based on the contract field."""
        field_lower = contract_field.lower()
        if "libero" in field_lower:
            return enums.CurrentAvailability.AVAILABLE
        elif "a reddito" in field_lower:
            return enums.CurrentAvailability.OCCUPIED
        return None

    def _parse_surface(self, surface_formatted: str) -> float:
        """Parse surface string to formatted string and float."""

        surface_formatted = surface_formatted.strip()
        # Check that the string ends with " m²"
        if not (surface_formatted.endswith("m²") or surface_formatted.endswith("sqm")):
            logger.warning("Surface string does not end with 'm²' or 'sqm': %s", surface_formatted)
            raise ValueError(f"Invalid surface format: {surface_formatted}")

        # Extract number from string like "35 m²", "35.5 sqm", or "35,5 m²"
        match = re.search(r"(\d+(?:[\.,]\d+)?)", surface_formatted)
        if match:
            num_str = match.group(1).replace(",", ".")
            try:
                surface_value = float(num_str)
            except ValueError as err:
                logger.warning("Could not parse numeric surface value: %s", num_str)
                raise ValueError(
                    f"Invalid surface format (unparseable number): {surface_formatted}"
                ) from err

            logger.debug("Parsed surface: %s -> (%.2f)", surface_formatted, surface_value)
            return surface_value
        logger.warning("Could not extract number from surface: %s", surface_formatted)
        raise ValueError(f"Invalid surface format (no numerical values): {surface_formatted}")

    def _parse_garden(self, garden_field: str | bool | None) -> enums.Garden | None:
        """Parse the 'garden' field."""
        if not garden_field or isinstance(garden_field, bool) or not garden_field.strip():
            return None
        garden_field = garden_field.strip()
        return self._parse_enumeration_field("garden", garden_field, GARDEN_MAP)

    def _parse_address(self, address: str) -> tuple[str | None, str | None]:
        """Parse the address into zone and street components."""
        if not address or address.strip() == "":
            return None, None
        address = address.strip()
        # Split the address into parts
        # Part 0 is the city, already extracted, will be ignored
        parts = [p.strip() for p in address.split('/')]
        zone = parts[1] if len(parts) >= 2 and parts[1] != "" else None
        street = parts[2] if len(parts) >= 3 and parts[2] != "" else None
        return zone, street

    def _map_other_features(self, features: list[str]) -> OtherFeatures | None:
        """Extract amenities from other_amenities columns and additional fields."""

        if not features or len(features) <= 0:
            return None

        amenities_dict = {}
        # Process other_amenities columns
        for amenity_value_raw in features:
            amenity_value = amenity_value_raw.strip()
            if not amenity_value:
                continue
            # Direct amenity mapping
            field_name = OTHER_FEATURES.get(amenity_value, None)
            if field_name:
                # Most cases are resolved here, just 3 exceptions.
                amenities_dict[field_name] = True
            elif "Esposizione" in amenity_value:
                amenities_dict["sun_exposure"] = amenity_value
            elif "Impianto tv" in amenity_value:
                amenities_dict["tv_system"] = self._parse_enumeration_field(
                    "tv_system", amenity_value, TV_MAP
                )
            elif "Infissi esterni" in amenity_value:
                amenities_dict["window_glass_type"], amenities_dict["window_material"] = (
                    self._extract_window_info(amenity_value)
                )
            else:
                logger.warning("Unknown amenity value: %s", amenity_value)
        return OtherFeatures(**amenities_dict) if amenities_dict else None

    def _extract_window_info(
        self, window_str: str
    ) -> tuple[enums.WindowGlassType | None, enums.WindowMaterial | None]:
        """Extract window glass type and material from amenity fields."""
        if not window_str or not window_str.strip():
            return None, None

        windows_info = [info.strip() for info in window_str.split("/") if info.strip()]

        # Handle empty result after filtering
        if not windows_info:
            return None, None

        # Extract glass type from first part
        glass_type = self._parse_glass_type(windows_info[0])

        # Extract material from second part if available
        material = None
        if len(windows_info) >= 2:
            material = self._parse_enumeration_field(
                "window_material", windows_info[1], WINDOW_MATERIAL_MAP
            )

        return glass_type, material

    def _parse_glass_type(self, glass_str: str) -> enums.WindowGlassType | None:
        """Parse glass type from glass description string."""
        if not glass_str:
            return None

        glass_lower = glass_str.lower()

        if "triplo vetro" in glass_lower:
            return enums.WindowGlassType.TRIPLE_GLASS
        elif "doppio vetro" in glass_lower:
            return enums.WindowGlassType.DOUBLE_GLASS
        elif "vetro" in glass_lower:
            return enums.WindowGlassType.SINGLE_GLASS
        else:
            logger.warning("Unknown window glass type in amenity: [%s]", glass_str)
            return None
