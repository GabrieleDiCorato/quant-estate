"""Source-specific mappers and translation tables.

This package contains:
- immobiliare_enum_mapper: Italian label -> internal Enum mappings (immutable)
- immobiliare_listing_mapper: ListingDetails -> ListingRecord transformer for Immobiliare.it
"""

from .immobiliare_enum_mapper import (
    IMM_PROPERTY_CONDITION_MAP,
    IMM_CONTRACT_TYPE_MAP,
    IMM_FURNITURE_MAP,
    IMM_GARDEN_MAP,
    IMM_KITCHEN_MAP,
    IMM_OWNERSHIP_MAP,
    IMM_PROPERTY_CLASS_MAP,
    IMM_PROPERTY_TYPE_MAP,
    IMM_TV_SYSTEM_MAP,
    IMM_WINDOW_MATERIAL_MAP,
    IMM_OTHER_FEATURES
)

from .immobiliare_listing_mapper import ListingDataTransformer
