"""
File containing all simple enumerations used in the project.
Common to all connectors and data models.
"""
from enum import Enum

class BaseEnum(str, Enum):
    """Base class for all enumerations in the project."""

    def __str__(self):
        return self.value

class Source(BaseEnum):
    """Enumeration for data source types."""
    IMMOBILIARE = "immobiliare"

class ContractType(BaseEnum):
    SALE = "sale"
    RENT = "rent"
    # "Acquisto con riscatto"
    RENT_TO_OWN = "rent_to_own"

class PropertyType(BaseEnum):
    APARTMENT = "apartment"
    HOUSE = "house"
    COMMERCIAL = "commercial"
    LAND = "land"
    INDUSTRIAL = "industrial"

class HeatingType(BaseEnum):
    CENTRAL = "central"
    INDEPENDENT = "independent"
    NONE = "none"

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

class AgencyType(BaseEnum):
    REAL_ESTATE = "real_estate"
    CONSTRUCTION = "construction"
    PROPERTY_MANAGEMENT = "property_management"
    INVESTMENT = "investment"
    OTHER = "other"

class RegionType(BaseEnum):
    URBAN = "urban"
    SUBURBAN = "suburban"
    RURAL = "rural"
    COASTAL = "coastal"
    MOUNTAIN = "mountain"
    DESERT = "desert"
