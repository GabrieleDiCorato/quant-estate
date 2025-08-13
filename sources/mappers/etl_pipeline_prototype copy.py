#!/usr/bin/env python3
"""
ETL Pipeline Prototype: ListingDetails to ListingRecord Mapping

This script demonstrates how to transform ListingDetails instances from CSV data
into normalized ListingRecord instances, handling data parsing, type conversion,
and enumeration mapping.
"""

import csv
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from sources.datamodel.listing_record import ListingRecord
import sources.datamodel.enumerations as enums

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ListingDataTransformer:
    """Transforms ListingDetails CSV data to ListingRecord instances."""

    def __init__(self):
        """Initialize the transformer with mapping dictionaries."""

        # Pre-populate mappings for efficiency
        self.condition_mapping = self._reverse_enum_mapping(enums.PropertyCondition)
        self.contract_type_mapping = self._reverse_enum_mapping(enums.ContractType)
        self.energy_class_mapping = self._reverse_enum_mapping(enums.EnergyClass)
        self.furniture_mapping = self._reverse_enum_mapping(enums.FurnitureType)
        self.garden_mapping = self._reverse_enum_mapping(enums.Garden)
        self.kitchen_mapping = self._reverse_enum_mapping(enums.KitchenType)
        self.ownership_type_mapping = self._reverse_enum_mapping(enums.OwnershipType)
        self.property_class_mapping = self._reverse_enum_mapping(enums.PropertyClass)
        self.property_type_mapping = self._reverse_enum_mapping(enums.PropertyType)
        self.tv_system_mapping = self._reverse_enum_mapping(enums.TvSystem)
        self.window_glass_mapping = self._reverse_enum_mapping(enums.WindowGlassType)
        self.window_material_mapping = self._reverse_enum_mapping(enums.WindowMaterial)

        # Only keep custom mappings for amenities since they map to boolean fields
        self.amenity_mapping = {
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
    def _reverse_enum_mapping(enum_mapping: type[enums.BaseEnum]) -> dict[str, enums.BaseEnum]:
        """Reverse the enum mapping to get a dictionary of value to enum."""
        return {enum.value: enum for enum in enum_mapping}

    def parse_composite_field(self, field_value: str, separator: str = " | ") -> List[str]:
        """Parse composite fields that contain multiple values separated by delimiters."""
        if not field_value or field_value.strip() == "":
            return []
        return [part.strip() for part in field_value.split(separator) if part.strip()]

    def parse_type_field(self, type_field: str) -> Dict[str, Any]:
        """Parse the 'type' field which contains property type, ownership, and class info."""
        parts = self.parse_composite_field(type_field)
        result = {}

        for part in parts:
            if part in self.property_type_mapping:
                result["property_type"] = self.property_type_mapping[part]
            elif part in self.ownership_type_mapping:
                result["ownership_type"] = self.ownership_type_mapping[part]
            elif part in self.property_class_mapping:
                result["property_class"] = self.property_class_mapping[part]

        return result

    def parse_contract_field(self, contract_field: str) -> Dict[str, Any]:
        """Parse the 'contract' field."""
        result = {}
        if contract_field in self.contract_type_mapping:
            result["contract_type"] = self.contract_type_mapping[contract_field]
        return result

    def safe_bool_conversion(self, value: Optional[str]) -> Optional[bool]:
        """Safely convert string values to boolean."""
        if not value or value.strip() == "":
            return None
        value_lower = value.lower().strip()
        if value_lower in ["true", "sì", "si", "yes", "1"]:
            return True
        elif value_lower in ["false", "no", "0"]:
            return False
        return None

    def safe_int_conversion(self, value: Optional[str]) -> Optional[int]:
        """Safely convert string values to integer."""
        if not value or value.strip() == "":
            return None
        try:
            return int(float(value))  # Handle cases where value might be "1.0"
        except (ValueError, TypeError):
            return None

    def safe_float_conversion(self, value: Optional[str]) -> Optional[float]:
        """Safely convert string values to float."""
        if not value or value.strip() == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
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

    def extract_zone_from_address(self, address: Optional[str]) -> Optional[str]:
        """Extract zone/neighborhood from address string."""
        if not address:
            return None

        # Look for patterns like "Milano/Zone/Street"
        parts = address.split('/')
        if len(parts) >= 2:
            return parts[1]  # Return the zone part
        return None

    def extract_amenities_from_csv_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Extract amenities from other_amenities columns and additional fields."""
        amenities = {}

        # Process other_amenities columns
        for i in range(8):  # other_amenities[0] through other_amenities[7]
            amenity_key = f"other_amenities[{i}]"
            if amenity_key in row and row[amenity_key]:
                amenity_value = row[amenity_key].strip()

                # Direct amenity mapping
                if amenity_value in self.amenity_mapping:
                    field_name = self.amenity_mapping[amenity_value]
                    amenities[field_name] = True

                # Handle composite amenity descriptions like "Infissi esterni in doppio vetro / PVC"
                self._parse_composite_amenity(amenity_value, amenities)

        # Extract window information from amenities
        window_info = self._extract_window_info(row)
        amenities.update(window_info)

        return amenities

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

    def _extract_window_info(self, row: Dict[str, str]) -> Dict[str, Any]:
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

    def transform_csv_row_to_listing_record(self, row: Dict[str, str]) -> Optional[ListingRecord]:
        """Transform a single CSV row to a ListingRecord instance."""
        try:
            # Validate required fields
            required_fields = ['id', 'source', 'price_eur', 'surface', 'city', 'type']
            for field in required_fields:
                if not row.get(field):
                    logger.warning(f"Missing required field '{field}' for listing {row.get('id', 'unknown')}")
                    return None

            # Parse composite fields
            type_info = self.parse_type_field(row.get('type', ''))
            contract_info = self.parse_contract_field(row.get('contract', ''))

            # Check if we got the required property_type from parsing
            if 'property_type' not in type_info:
                logger.warning(f"Could not parse property_type from '{row.get('type', '')}' for listing {row.get('id', 'unknown')}")
                return None

            # Check if we got the required contract_type from parsing
            if 'contract_type' not in contract_info:
                logger.warning(f"Could not parse contract_type from '{row.get('contract', '')}' for listing {row.get('id', 'unknown')}")
                return None

            # Extract amenities
            amenities = self.extract_amenities_from_csv_row(row)

            # Build the data dictionary for ListingRecord
            data = {
                # Core identifier
                "id": row['id'],
                "source": row['source'],
                "title": row.get('title', ''),
                "url": row.get('url', ''),
                
                # Timestamps
                "timestamp": datetime.now(tz=ZoneInfo("Europe/Rome")),
                "last_updated": self.parse_datetime(row.get('last_updated')),
                
                # Pricing
                "price_eur": self.safe_float_conversion(row['price_eur']),
                "maintenance_fee": self.safe_float_conversion(row.get('maintenance_fee')),
                "price_sqm": self.safe_float_conversion(row.get('price_sqm')),
                
                # Property classification from parsed fields
                "contract_type": contract_info.get("contract_type"),
                "is_rent_to_own_available": False,  # Default value
                "current_availability": enums.CurrentAvailability.AVAILABLE,  # Default value
                "is_luxury": row.get('is_luxury') == 'true' if row.get('is_luxury') else None,
                
                # Property condition
                "condition": self.condition_mapping.get(row.get('condition') or ''),
                
                # Property details
                "surface": self.safe_float_conversion(row['surface']),
                "rooms": self.safe_int_conversion(row.get('rooms')),
                "floor": row.get('floor'),
                "total_floors": self.safe_int_conversion(row.get('total_floors')),
                
                # Composition
                "bathrooms": self.safe_int_conversion(row.get('bathrooms')),
                "bedrooms": self.safe_int_conversion(row.get('bedrooms')),
                "has_balcony": self.safe_bool_conversion(row.get('balcony')),
                "has_terrace": self.safe_bool_conversion(row.get('terrace')),
                "has_elevator": self.safe_bool_conversion(row.get('elevator')),
                "garden": self.garden_mapping.get(row.get('garden') or ''),
                "has_cellar": self.safe_bool_conversion(row.get('cellar')),
                "has_basement": None,  # Not in CSV, could be derived
                "furnished": self.furniture_mapping.get(row.get('furnished') or ''),
                "kitchen": self.kitchen_mapping.get(row.get('kitchen') or ''),
                
                # Building info
                "build_year": self.safe_int_conversion(row.get('build_year')),
                "has_concierge": self.safe_bool_conversion(row.get('concierge')),
                "is_accessible": self.safe_bool_conversion(row.get('is_accessible')),
                
                # Energy and utilities
                "heating_type": row.get('heating_type'),
                "air_conditioning": row.get('air_conditioning'),
                "energy_class": enums.EnergyClass(row['energy_class']) if row.get('energy_class') else None,
                
                # Location
                "country": row.get('country', 'IT'),  # Default to Italy
                "city": row['city'],
                "zone": self.extract_zone_from_address(row.get('address')),
                "address": row.get('address'),
                
                # Parking - not in CSV
                "parking_info": None,
                
                # Description
                "description_title": row.get('description_title'),
                "description": row.get('description', ''),
            }

            # Add type information from parsed composite field
            data.update(type_info)

            # Add amenities
            data.update(amenities)

            # Create and validate ListingRecord
            return ListingRecord.model_validate(data)

        except Exception as e:
            logger.error(f"Error transforming row for listing {row.get('id', 'unknown')}: {e}")
            return None


def load_csv_and_transform(csv_file_path: Path) -> List[ListingRecord]:
    """Load CSV file and transform all rows to ListingRecord instances."""
    transformer = ListingDataTransformer()
    records = []
    
    logger.info(f"Loading CSV file: {csv_file_path}")
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        total_rows = 0
        successful_transformations = 0
        
        for row in reader:
            total_rows += 1
            record = transformer.transform_csv_row_to_listing_record(row)
            
            if record:
                records.append(record)
                successful_transformations += 1
            
            # Log progress every 100 records
            if total_rows % 100 == 0:
                logger.info(f"Processed {total_rows} rows, {successful_transformations} successful transformations")
    
    logger.info(f"Transformation complete: {successful_transformations}/{total_rows} records transformed successfully")
    return records


def validate_transformations(records: List[ListingRecord]) -> None:
    """Validate the transformed records and report statistics."""
    if not records:
        logger.warning("No records to validate")
        return
    
    logger.info(f"Validating {len(records)} transformed records...")
    
    # Basic statistics
    property_types = {}
    contract_types = {}
    cities = {}
    
    for record in records:
        # Count property types
        prop_type = str(record.property_type) if record.property_type else "Unknown"
        property_types[prop_type] = property_types.get(prop_type, 0) + 1
        
        # Count contract types
        contract_type = str(record.contract_type) if record.contract_type else "Unknown"
        contract_types[contract_type] = contract_types.get(contract_type, 0) + 1
        
        # Count cities
        cities[record.city] = cities.get(record.city, 0) + 1
    
    logger.info("=== Transformation Statistics ===")
    logger.info(f"Total records: {len(records)}")
    
    logger.info("Property Types:")
    for prop_type, count in sorted(property_types.items()):
        logger.info(f"  {prop_type}: {count}")
    
    logger.info("Contract Types:")
    for contract_type, count in sorted(contract_types.items()):
        logger.info(f"  {contract_type}: {count}")
    
    logger.info("Cities (top 5):")
    for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5]:
        logger.info(f"  {city}: {count}")


def save_transformed_records(records: List[ListingRecord], output_file: Path) -> None:
    """Save transformed records to a CSV file."""
    if not records:
        logger.warning("No records to save")
        return
    
    logger.info(f"Saving {len(records)} transformed records to {output_file}")
    
    # Convert records to dictionaries
    data_dicts = [record.model_dump() for record in records]
    
    # Get all field names from the first record
    fieldnames = list(data_dicts[0].keys()) if data_dicts else []
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_dicts)
    
    logger.info(f"Successfully saved {len(records)} records to {output_file}")


def compare_record_sample(original_row: Dict[str, str], transformed_record: ListingRecord) -> None:
    """Compare original CSV data with transformed record to show the mapping."""
    logger.info("=== Mapping Comparison Example ===")
    logger.info(f"Original ID: {original_row.get('id', 'N/A')}")
    logger.info(f"Transformed ID: {transformed_record.id}")
    
    logger.info(f"Original Type: {original_row.get('type', 'N/A')}")
    logger.info(f"Transformed Property Type: {transformed_record.property_type}")
    logger.info(f"Transformed Ownership Type: {transformed_record.ownership_type}")
    logger.info(f"Transformed Property Class: {transformed_record.property_class}")
    
    logger.info(f"Original Contract: {original_row.get('contract', 'N/A')}")
    logger.info(f"Transformed Contract Type: {transformed_record.contract_type}")
    
    logger.info(f"Original Price: {original_row.get('formatted_price', 'N/A')}")
    logger.info(f"Transformed Price: €{transformed_record.price_eur:,.0f}")
    
    logger.info(f"Original Surface: {original_row.get('surface_formatted', 'N/A')}")
    logger.info(f"Transformed Surface: {transformed_record.surface} m²")
    
    logger.info(f"Original Condition: {original_row.get('condition', 'N/A')}")
    logger.info(f"Transformed Condition: {transformed_record.condition}")
    
    # Show amenity mapping example
    amenities_found = []
    for i in range(8):
        amenity_key = f"other_amenities[{i}]"
        if amenity_key in original_row and original_row[amenity_key]:
            amenities_found.append(original_row[amenity_key])
    
    if amenities_found:
        logger.info(f"Original Amenities: {', '.join(amenities_found[:3])}")
        amenity_fields = []
        if transformed_record.has_fiber_optic:
            amenity_fields.append("has_fiber_optic=True")
        if transformed_record.has_armored_door:
            amenity_fields.append("has_armored_door=True")
        if transformed_record.has_video_intercom:
            amenity_fields.append("has_video_intercom=True")
        if amenity_fields:
            logger.info(f"Transformed Amenity Fields: {', '.join(amenity_fields[:3])}")


def main():
    """Main execution function."""
    # Path to the CSV file
    csv_file_path = Path("notebooks/data/quant_estate.listings.csv")
    
    if not csv_file_path.exists():
        logger.error(f"CSV file not found: {csv_file_path}")
        return
    
    # Transform the data
    records = load_csv_and_transform(csv_file_path)
    
    # Validate the transformations
    validate_transformations(records)
    
    # Example: Print first few transformed records
    if records:
        logger.info("=== Sample Transformed Records ===")
        for i, record in enumerate(records[:3]):
            logger.info(f"Record {i+1}:")
            logger.info(f"  ID: {record.id}")
            logger.info(f"  Property Type: {record.property_type}")
            logger.info(f"  Contract Type: {record.contract_type}")
            logger.info(f"  Price: €{record.price_eur:,.0f}")
            logger.info(f"  Surface: {record.surface} m²")
            logger.info(f"  City: {record.city}")
            logger.info(f"  Condition: {record.condition}")
            logger.info("---")
        
        # Show detailed mapping comparison for first record
        transformer = ListingDataTransformer()
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            first_row = next(reader)
            compare_record_sample(first_row, records[0])
        
        # Save transformed records
        output_path = Path("notebooks/data/transformed_listing_records.csv")
        save_transformed_records(records, output_path)


if __name__ == "__main__":
    main()
