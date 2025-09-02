"""
File containing all simple enumerations used in the project.
Common to all scrapers and data models.
"""

from enum import Enum


class BaseEnum(str, Enum):
    """Base class for all enumerations in the project."""

    def __str__(self) -> str:
        return self.value


class AirConditioningType(BaseEnum):
    CENTRAL = "central"
    INDEPENDENT = "independent"
    NONE = "none"


class ConditionType(BaseEnum):
    NEW = "new"
    GOOD = "good"
    RENOVATED = "renovated"
    TO_RENOVATE = "to_renovate"
    OLD = "old"


class ContractType(BaseEnum):
    SALE = "sale"
    RENT = "rent"


class CurrentAvailability(BaseEnum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"


class EnergyClass(BaseEnum):
    A = "A"
    AP = "A+"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class FurnitureType(BaseEnum):
    PARTIALLY_FURNISHED = "partially_furnished"
    FULLY_FURNISHED = "fully_furnished"
    ONLY_KITCHEN = "only_kitchen"
    NO = "none"


class Garden(BaseEnum):
    """Garden types for property listings."""

    PRIVATE = "private"
    SHARED = "shared"
    NONE = "none"


class HeatingType(BaseEnum):
    CENTRAL = "central"
    INDEPENDENT = "independent"
    NONE = "none"


class KitchenType(BaseEnum):
    """Kitchen types for property listings."""

    HABITABLE = "habitable"
    OPEN_VIEW = "open_view"
    KITCHENETTE = "kitchenette"
    COOKING_CORNER = "kitchen_corner"
    SEMI_HABITABLE = "semi_habitable"


class OwnershipType(BaseEnum):
    """Types of property ownership in Italian real estate."""

    FULL_OWNERSHIP = "full_ownership"
    BARE_OWNERSHIP = "bare_ownership"
    SURFACE_RIGHT = "surface_right"


class PropertyClass(BaseEnum):
    """Property class classification based on quality and market positioning."""

    LUXURY = "upscale"
    MEDIUM = "medium"
    ECONOMIC = "economic"
    HIGH_END_LUXURY = "luxury"


class PropertyCondition(BaseEnum):
    """Property condition classification."""

    EXCELLENT_RENOVATED = "excellent_renovated"
    TO_RENOVATE = "to_renovate"
    NEW_UNDER_CONSTRUCTION = "new_under_construction"
    GOOD_HABITABLE = "good_habitable"


class PropertyType(BaseEnum):
    """Italian property subtypes for detailed classification."""

    APARTMENT = "apartment"
    PENTHOUSE = "penthouse"
    LOFT = "loft"
    SEMI_DETACHED_VILLA = "semi_detached_villa"
    ATTIC = "attic"
    DETACHED_VILLA = "detached_villa"
    OPEN_SPACE = "open_space"
    TERRACED_HOUSE = "terraced_house"
    TOWNHOUSE = "townhouse"
    VILLA_APARTMENT = "villa_apartment"
    MULTI_FAMILY_VILLA = "multi_family_villa"
    RUSTIC_HOUSE = "rustic_house"


class RegionType(BaseEnum):
    URBAN = "urban"
    SUBURBAN = "suburban"
    RURAL = "rural"
    COASTAL = "coastal"
    MOUNTAIN = "mountain"
    DESERT = "desert"


class Source(BaseEnum):
    """Enumeration for data source types."""

    IMMOBILIARE = "immobiliare"


class TvSystem(BaseEnum):
    """TV system types for property listings."""

    CENTRALIZED = "centralized"
    SATELLITE = "satellite"
    INDIVIDUAL = "individual"


class WindowGlassType(BaseEnum):
    """Window glass types for property listings."""

    SINGLE_GLASS = "single_glass"
    DOUBLE_GLASS = "double_glass"
    TRIPLE_GLASS = "triple_glass"


class WindowMaterial(BaseEnum):
    """Window frame materials for property listings."""

    WOOD = "wood"
    METAL = "metal"
    PVC = "pvc"
