"""
Italian string -> Enum value mappings for Immobiliare.it source.

These dictionaries translate the exact Italian labels found on immobiliare.it
into our internal, JSON-friendly enum values defined in sources.datamodel.enumerations.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from sources.datamodel.enumerations import (
    AirConditioningType,
    ContractType,
    CurrentAvailability,
    EnergyClass,
    FurnitureType,
    Garden,
    HeatingType,
    KitchenType,
    OwnershipType,
    PropertyClass,
    PropertyCondition,
    PropertyType,
    RegionType,
    TvSystem,
    WindowMaterial,
)

# FurnitureType
_IMM_FURNITURE_MAP: dict[str, FurnitureType] = {
    "Sì": FurnitureType.FULLY_FURNISHED,
    "Parzialmente Arredato": FurnitureType.PARTIALLY_FURNISHED,
    "Solo Cucina Arredata": FurnitureType.ONLY_KITCHEN,
    "No": FurnitureType.NO,
}
IMM_FURNITURE_MAP: Final[Mapping[str, FurnitureType]] = MappingProxyType(_IMM_FURNITURE_MAP)

# Garden
_IMM_GARDEN_MAP: dict[str, Garden] = {
    "Giardino privato": Garden.PRIVATE,
    "Giardino comune": Garden.SHARED,
    "Nessun giardino": Garden.NONE,
    # TODO remove
    "FALSE": Garden.NONE,  # backward compatibility
}
IMM_GARDEN_MAP: Final[Mapping[str, Garden]] = MappingProxyType(_IMM_GARDEN_MAP)

# KitchenType
_IMM_KITCHEN_MAP: dict[str, KitchenType] = {
    "Cucina abitabile": KitchenType.HABITABLE,
    "Cucina a vista": KitchenType.OPEN_VIEW,
    "Cucina cucinotto": KitchenType.KITCHENETTE,
    "Cucina angolo cottura": KitchenType.COOKING_CORNER,
    "Cucina semi abitabile": KitchenType.SEMI_HABITABLE,
}
IMM_KITCHEN_MAP: Final[Mapping[str, KitchenType]] = MappingProxyType(_IMM_KITCHEN_MAP)

# OwnershipType
_IMM_OWNERSHIP_MAP: dict[str, OwnershipType] = {
    "Intera proprietà": OwnershipType.FULL_OWNERSHIP,
    "Nuda proprietà": OwnershipType.BARE_OWNERSHIP,
    "Diritto di superficie": OwnershipType.SURFACE_RIGHT,
}
IMM_OWNERSHIP_MAP: Final[Mapping[str, OwnershipType]] = MappingProxyType(_IMM_OWNERSHIP_MAP)

# PropertyClass
_IMM_PROPERTY_CLASS_MAP: dict[str, PropertyClass] = {
    "Classe immobile signorile": PropertyClass.LUXURY,
    "Classe immobile media": PropertyClass.MEDIUM,
    "Classe immobile economica": PropertyClass.ECONOMIC,
    "Immobile di lusso": PropertyClass.HIGH_END_LUXURY,
}
IMM_PROPERTY_CLASS_MAP: Final[Mapping[str, PropertyClass]] = MappingProxyType(_IMM_PROPERTY_CLASS_MAP)

# PropertyCondition
_IMM_PROPERTY_CONDITION_MAP: dict[str, PropertyCondition] = {
    "Ottimo / Ristrutturato": PropertyCondition.EXCELLENT_RENOVATED,
    "Da ristrutturare": PropertyCondition.TO_RENOVATE,
    "Nuovo / In costruzione": PropertyCondition.NEW_UNDER_CONSTRUCTION,
    "Buono / Abitabile": PropertyCondition.GOOD_HABITABLE,
}
IMM_PROPERTY_CONDITION_MAP: Final[Mapping[str, PropertyCondition]] = MappingProxyType(_IMM_PROPERTY_CONDITION_MAP)

# PropertyType
_IMM_PROPERTY_TYPE_MAP: dict[str, PropertyType] = {
    "Appartamento": PropertyType.APARTMENT,
    "Attico": PropertyType.PENTHOUSE,
    "Loft": PropertyType.LOFT,
    "Villa bifamiliare": PropertyType.SEMI_DETACHED_VILLA,
    "Mansarda": PropertyType.ATTIC,
    "Villa unifamiliare": PropertyType.DETACHED_VILLA,
    "Open space": PropertyType.OPEN_SPACE,
    "Terratetto unifamiliare": PropertyType.TERRACED_HOUSE,
    "Villa a schiera": PropertyType.TOWNHOUSE,
    "Appartamento in villa": PropertyType.VILLA_APARTMENT,
    "Villa plurifamiliare": PropertyType.MULTI_FAMILY_VILLA,
    "Rustico": PropertyType.RUSTIC_HOUSE,
}
IMM_PROPERTY_TYPE_MAP: Final[Mapping[str, PropertyType]] = MappingProxyType(_IMM_PROPERTY_TYPE_MAP)

# TvSystem
_IMM_TV_SYSTEM_MAP: dict[str, TvSystem] = {
    "Impianto tv centralizzato": TvSystem.CENTRALIZED,
    "Impianto tv con parabola satellitare": TvSystem.SATELLITE,
    "Impianto tv singolo": TvSystem.INDIVIDUAL,
}
IMM_TV_SYSTEM_MAP: Final[Mapping[str, TvSystem]] = MappingProxyType(_IMM_TV_SYSTEM_MAP)

# WindowMaterial (comes embedded in amenities text)
_IMM_WINDOW_MATERIAL_MAP: dict[str, WindowMaterial] = {
    "legno": WindowMaterial.WOOD,
    "metallo": WindowMaterial.METAL,
    "PVC": WindowMaterial.PVC,
}
IMM_WINDOW_MATERIAL_MAP: Final[Mapping[str, WindowMaterial]] = MappingProxyType(_IMM_WINDOW_MATERIAL_MAP)

# Identity or simple mappings for enums already in English (if needed in future)
_IMM_CONTRACT_TYPE_MAP: dict[str, ContractType] = {
    "Vendita": ContractType.SALE,
    "Affitto": ContractType.RENT,
}
IMM_CONTRACT_TYPE_MAP: Final[Mapping[str, ContractType]] = MappingProxyType(_IMM_CONTRACT_TYPE_MAP)

_IMM_AIR_CONDITIONING_MAP: dict[str, AirConditioningType] = {
    "centralizzato": AirConditioningType.CENTRAL,
    "autonomo": AirConditioningType.INDEPENDENT,
    "assenza": AirConditioningType.NONE,
}
IMM_AIR_CONDITIONING_MAP: Final[Mapping[str, AirConditioningType]] = MappingProxyType(_IMM_AIR_CONDITIONING_MAP)

_IMM_HEATING_MAP: dict[str, HeatingType] = {
    "centralizzato": HeatingType.CENTRAL,
    "autonomo": HeatingType.INDEPENDENT,
    "assenza": HeatingType.NONE,
}
IMM_HEATING_MAP: Final[Mapping[str, HeatingType]] = MappingProxyType(_IMM_HEATING_MAP)

# Energy class labels are already A, A+, etc.
_IMM_ENERGY_CLASS_MAP: dict[str, EnergyClass] = {e.value: e for e in EnergyClass}
IMM_ENERGY_CLASS_MAP: Final[Mapping[str, EnergyClass]] = MappingProxyType(_IMM_ENERGY_CLASS_MAP)

# For completeness, keep placeholders for enums not typically labeled from site text
_IMM_CURRENT_AVAILABILITY_MAP: dict[str, CurrentAvailability] = {
    "disponibile": CurrentAvailability.AVAILABLE,
    "occupato": CurrentAvailability.OCCUPIED,
}
IMM_CURRENT_AVAILABILITY_MAP: Final[Mapping[str, CurrentAvailability]] = MappingProxyType(_IMM_CURRENT_AVAILABILITY_MAP)

_IMM_REGION_MAP: dict[str, RegionType] = {
    "urbano": RegionType.URBAN,
    "suburbano": RegionType.SUBURBAN,
    "rurale": RegionType.RURAL,
    "costiero": RegionType.COASTAL,
    "montano": RegionType.MOUNTAIN,
    "deserto": RegionType.DESERT,
}
IMM_REGION_MAP: Final[Mapping[str, RegionType]] = MappingProxyType(_IMM_REGION_MAP)

_IMM_OTHER_FEATURES: dict[str, str] = {
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
IMM_OTHER_FEATURES: Final[Mapping[str, str]] = MappingProxyType(_IMM_OTHER_FEATURES)
