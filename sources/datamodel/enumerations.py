"""
File containing all simple enumerations used in the project.
Common to all connectors and data models.
"""
from enum import Enum


class BaseEnum(str, Enum):
    """Base class for all enumerations in the project."""

    def __str__(self):
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
    PARTIALLY_FURNISHED = "Parzialmente arredato"
    FULLY_FURNISHED = "Completamente arredato"
    ONLY_KITCHEN = "Solo cucina arredata"
    NO = "No"


class Garden(BaseEnum):
    """Garden types for property listings."""
    PRIVATE = "Giardino privato"
    SHARED = "Giardino comune"
    NONE = "Nessun giardino"


class HeatingType(BaseEnum):
    CENTRAL = "central"
    INDEPENDENT = "independent"
    NONE = "none"


class KitchenType(BaseEnum):
    """Kitchen types for property listings."""
    HABITABLE = "Cucina abitabile"
    OPEN_VIEW = "Cucina a vista"
    KITCHENETTE = "Cucina cucinotto"
    COOKING_CORNER = "Cucina angolo cottura"
    SEMI_HABITABLE = "Cucina semi abitabile"


class OwnershipType(BaseEnum):
    """Types of property ownership in Italian real estate."""
    FULL_OWNERSHIP = "Intera proprietà"
    BARE_OWNERSHIP = "Nuda proprietà"


class PropertyClass(BaseEnum):
    """Property class classification based on quality and market positioning."""
    LUXURY = "Classe immobile signorile"
    MEDIUM = "Classe immobile media"
    ECONOMIC = "Classe immobile economica"
    HIGH_END_LUXURY = "Immobile di lusso"


class PropertyCondition(BaseEnum):
    """Property condition classification."""
    EXCELLENT_RENOVATED = "Ottimo / Ristrutturato"
    TO_RENOVATE = "Da ristrutturare"
    NEW_UNDER_CONSTRUCTION = "Nuovo / In costruzione"
    GOOD_HABITABLE = "Buono / Abitabile"


class PropertyType(BaseEnum):
    """Italian property subtypes for detailed classification."""
    APARTMENT = "Appartamento"
    PENTHOUSE = "Attico"
    LOFT = "Loft"
    SEMI_DETACHED_VILLA = "Villa bifamiliare"
    ATTIC = "Mansarda"
    DETACHED_VILLA = "Villa unifamiliare"
    OPEN_SPACE = "Open space"
    TERRACED_HOUSE = "Terratetto unifamiliare"
    TOWNHOUSE = "Villa a schiera"
    VILLA_APARTMENT = "Appartamento in villa"
    MULTI_FAMILY_VILLA = "Villa plurifamiliare"
    RUSTIC_HOUSE = "Rustico"


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
    CENTRALIZED = "Impianto tv centralizzato"
    SATELLITE = "Impianto tv con parabola satellitare"
    INDIVIDUAL = "Impianto tv singolo"


class WindowGlassType(BaseEnum):
    """Window glass types for property listings."""
    SINGLE_GLASS = "vetro"
    DOUBLE_GLASS = "doppio vetro"
    TRIPLE_GLASS = "triplo vetro"


class WindowMaterial(BaseEnum):
    """Window frame materials for property listings."""
    WOOD = "legno"
    METAL = "metallo"
    PVC = "PVC"
