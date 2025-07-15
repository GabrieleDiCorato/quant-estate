"""
Logging utilities for the quant-estate project.
Configure logging once at application startup.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

# Global flag to prevent multiple configurations
_logging_configured = False


class LoggingConfigError(Exception):
    """Exception raised when logging configuration is invalid."""
    pass


def setup_logging(config: dict[str, Any] | None = None) -> None:
    """Setup logging configuration globally (call once at startup).
    
    Args:
        config: Optional logging configuration dict. If None, uses default config.
        
    Raises:
        LoggingConfigError: If custom config is provided but missing required fields.
    """
    global _logging_configured

    if _logging_configured:
        return

    if config is None:
        raise LoggingConfigError("No logging configuration provided")

    # Validate custom config has all required fields
    _validate_custom_config(config)

    _apply_logging_config(config)
    _logging_configured = True


def _validate_custom_config(config: dict[str, Any]) -> None:
    """Validate that custom config has all required fields.
    
    Args:
        config: Custom logging configuration
        
    Raises:
        LoggingConfigError: If required fields are missing
    """
    required_fields = ["level", "format", "date_format", "handlers"]
    
    for field in required_fields:
        if field not in config:
            raise LoggingConfigError(f"Required field '{field}' missing from custom logging config")
    
    # Validate handlers structure
    if not isinstance(config["handlers"], dict):
        raise LoggingConfigError("'handlers' must be a dictionary")
    
    # Check if at least one handler is configured
    if not config["handlers"]:
        raise LoggingConfigError("At least one handler must be configured")
    
    # Validate each handler configuration
    for handler_name, handler_config in config["handlers"].items():
        if not isinstance(handler_config, dict):
            raise LoggingConfigError(f"Handler '{handler_name}' config must be a dictionary")
        
        if "enabled" not in handler_config:
            raise LoggingConfigError(f"Handler '{handler_name}' missing required 'enabled' field")
        
        if "level" not in handler_config:
            raise LoggingConfigError(f"Handler '{handler_name}' missing required 'level' field")
        
        # Validate file handler specific fields
        if handler_name == "file" and handler_config.get("enabled", False):
            file_required = ["filename", "directory"]
            for field in file_required:
                if field not in handler_config:
                    raise LoggingConfigError(f"File handler missing required field '{field}'")


def _apply_logging_config(log_config: dict[str, Any]) -> None:
    """Apply the logging configuration to the root logger.
    
    Args:
        log_config: Dictionary containing logging configuration
        
    Raises:
        LoggingConfigError: If config values are invalid
    """
    try:
        # Get logging settings - no defaults when using custom config
        log_level = getattr(logging, log_config["level"].upper())
        log_format = log_config["format"]
        date_format = log_config["date_format"]
    except AttributeError as e:
        raise LoggingConfigError(f"Invalid logging level '{log_config['level']}': {e}")
    except KeyError as e:
        raise LoggingConfigError(f"Missing required config field: {e}")

    # Create formatter
    formatter = logging.Formatter(log_format, date_format)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler if enabled
    console_config = log_config["handlers"].get("console", {})
    if console_config.get("enabled", False):
        _add_console_handler(root_logger, formatter, console_config)

    # Add file handler if enabled
    file_config = log_config["handlers"].get("file", {})
    if file_config.get("enabled", False):
        _add_file_handler(root_logger, formatter, file_config)


def _add_console_handler(
    logger: logging.Logger, 
    formatter: logging.Formatter, 
    console_config: dict[str, Any]
) -> None:
    """Add console handler to the logger.
    
    Args:
        logger: The logger to add the handler to
        formatter: The formatter to use
        console_config: Console handler configuration
        
    Raises:
        LoggingConfigError: If console config is invalid
    """
    try:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(
            getattr(logging, console_config["level"].upper())
        )
        logger.addHandler(console_handler)
    except KeyError as e:
        raise LoggingConfigError(f"Console handler missing required field: {e}")
    except AttributeError as e:
        raise LoggingConfigError(f"Invalid console handler level '{console_config['level']}': {e}")


def _add_file_handler(
    logger: logging.Logger, 
    formatter: logging.Formatter,
    file_config: dict[str, Any]
) -> None:
    """Add file handler to the logger.
    
    Args:
        logger: The logger to add the handler to
        formatter: The formatter to use
        file_config: File handler configuration
        
    Raises:
        LoggingConfigError: If file config is invalid
    """
    try:
        # Create logs directory
        project_root = Path(__file__).parent.parent.parent
        logs_dir = project_root / file_config["directory"]
        logs_dir.mkdir(exist_ok=True)

        # Create log file with date
        date_str = datetime.now().strftime(file_config.get("date_format", "%Y-%m-%d"))
        filename = file_config["filename"].format(date=date_str)
        log_file = logs_dir / filename

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(
            getattr(logging, file_config["level"].upper())
        )
        logger.addHandler(file_handler)
    except KeyError as e:
        raise LoggingConfigError(f"File handler missing required field: {e}")
    except AttributeError as e:
        raise LoggingConfigError(f"Invalid file handler level '{file_config['level']}': {e}")
    except Exception as e:
        raise LoggingConfigError(f"Error creating file handler: {e}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (typically use __name__)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


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
