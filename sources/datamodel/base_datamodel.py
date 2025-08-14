"""
Basic data model configuration for our real estate application.
"""

from pydantic import BaseModel, ConfigDict


class QuantEstateDataObject(BaseModel):
    """Base class for all data objects in the QuantEstate application."""

    # Configuration: immutable, no extra fields, and performance optimizations
    model_config = ConfigDict(
        # Data processing
        str_strip_whitespace=True,
        validate_assignment=False,
        validate_default=True,
        allow_inf_nan=False,
        # Schema generation
        extra="forbid",
        frozen=True,
        # Performance & looks
        cache_strings=True,
        # Fundamental for mongo compatibility
        use_enum_values=True,
    )
