"""
Base classes and utilities for connectors.
"""

from .base import BaseConnector, BaseStorage, BaseScraper
from ..configs import ConfigManager

__all__ = ['BaseConnector', 'BaseStorage', 'BaseScraper', 'ConfigManager']