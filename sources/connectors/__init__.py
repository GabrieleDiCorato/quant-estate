"""
Base classes and utilities for connectors.
"""

from .base import BaseConnector, BaseStorage, BaseScraper
from ..config import ConfigManager

__all__ = ['BaseConnector', 'BaseStorage', 'BaseScraper', 'ConfigManager']