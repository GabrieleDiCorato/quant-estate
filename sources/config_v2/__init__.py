"""
Configuration package for the quant-estate project.
"""

# Import and expose both ConfigManager versions
from .pydantic_config_manager import PydanticConfigManager

__all__ = ['PydanticConfigManager'] 