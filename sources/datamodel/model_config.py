"""
Basic data model configuration for our real estate application.
"""

from pydantic import BaseModel, ConfigDict

class BaseModelWithConfig(BaseModel):
    """Data model for a real estate property."""

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
        use_enum_values=True
    )
