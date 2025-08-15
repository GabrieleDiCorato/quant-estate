"""
Base data model configuration and utilities shared across domain objects.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict


class QuantEstateDataObject(BaseModel):
    """Base class for all typed data objects in QuantEstate (Pydantic v2)."""

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
        # Use enum raw values for easy MongoDB storage and CSV export
        use_enum_values=True,
    )

    @classmethod
    def get_timestamp(cls) -> datetime:
        """Current timestamp in Europe/Rome timezone (naive-safe dt)."""
        return datetime.now(tz=ZoneInfo("Europe/Rome"))
