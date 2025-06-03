"""
Quant Estate - Real estate data collection and analysis toolkit
"""

__version__ = "0.1.0"

from .connectors import BaseConnector, BaseStorage, BaseScraper
from .config import ConfigManager

__all__ = [
    'BaseConnector',
    'BaseStorage',
    'BaseScraper',
    'ConfigManager',
    '__version__'
]