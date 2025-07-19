"""
Logging utilities for the quant-estate project.
Configure logging once at application startup using standard Python logging configuration.
"""

from __future__ import annotations

import logging
import logging.config
import yaml
from pathlib import Path
from datetime import datetime
from typing import Any

# Global flag to prevent multiple configurations
_logging_configured = False


class LoggingConfigError(Exception):
    """Exception raised when logging configuration is invalid."""
    pass


def setup_logging(config_path: str | Path | None = None) -> None:
    """Setup logging configuration globally (call once at startup).
    
    Args:
        config_path: Path to YAML logging configuration file. 
                    If None, uses default configuration.
        
    Raises:
        LoggingConfigError: If configuration file is invalid or missing.
    """
    global _logging_configured

    if _logging_configured:
        return

    if config_path is None:
        project_root = Path(__file__).parents[2]
        config_path = project_root / "sources" / "resources" / "logging.yaml"
    else:
        config_path = Path(config_path)

    # Make path absolute if it's relative
    if not config_path.is_absolute():
        project_root = Path(__file__).parents[2]
        config_path = project_root / config_path

    if not config_path.exists():
        raise LoggingConfigError(f"Logging configuration file not found: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise LoggingConfigError(f"Invalid YAML in logging configuration: {e}")
    except Exception as e:
        raise LoggingConfigError(f"Error reading logging configuration: {e}")

    # Add timestamp to filename if file handler exists
    if 'handlers' in config and 'file' in config['handlers']:
        _add_timestamp_to_filename(config['handlers']['file'])

    try:
        logging.config.dictConfig(config)
    except Exception as e:
        raise LoggingConfigError(f"Error applying logging configuration: {e}")

    _logging_configured = True


def _add_timestamp_to_filename(file_handler_config: dict[str, Any]) -> None:
    """Add timestamp to log filename if it contains a placeholder.
    
    Args:
        file_handler_config: File handler configuration dictionary
    """
    filename = file_handler_config.get('filename', '')
    if '{timestamp}' in filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_handler_config['filename'] = filename.format(timestamp=timestamp)
    
    # Ensure log directory exists
    log_path = Path(file_handler_config['filename'])
    log_path.parent.mkdir(parents=True, exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (typically use __name__)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


def get_module_logger() -> logging.Logger:
    """Get a logger for the calling module.
    
    Returns:
        logging.Logger: Logger instance named after the calling module
    """
    import inspect
    frame = inspect.currentframe()
    if frame and frame.f_back:
        module_name = frame.f_back.f_globals.get('__name__', 'unknown')
    else:
        module_name = 'unknown'
    return logging.getLogger(module_name)


def get_class_logger(cls: type) -> logging.Logger:
    """Get a logger instance for a class.
    
    Args:
        cls: The class to get a logger for
        
    Returns:
        logging.Logger: Logger instance named after the class
    """
    return logging.getLogger(f"{cls.__module__}.{cls.__name__}")


def is_logging_configured() -> bool:
    """Check if logging has been configured.
    
    Returns:
        bool: True if logging has been configured
    """
    return _logging_configured


def reset_logging_configuration() -> None:
    """Reset the logging configuration flag.
    
    Warning: Only use this for testing purposes.
    """
    global _logging_configured
    _logging_configured = False
