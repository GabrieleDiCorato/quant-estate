"""
Configuration package for the quant-estate project.
"""

from pathlib import Path

# Get the absolute path to the configs directory
CONFIGS_DIR = Path(__file__).parent.absolute()

# Get the absolute path to the connectors configs directory
CONNECTORS_CONFIGS_DIR = CONFIGS_DIR / 'connectors' 