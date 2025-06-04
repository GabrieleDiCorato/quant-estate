"""
Logging utilities for the quant-estate project.
"""

import logging
import sys
import inspect
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Type

def get_module_logger() -> logging.Logger:
    """Get a logger instance for the current module.
    
    This function should be used at the module level to get a logger
    that automatically uses the module's name.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    frame = inspect.currentframe()
    if frame is None:
        return logging.getLogger(__name__)
    module = inspect.getmodule(frame.f_back)
    if module is None:
        return logging.getLogger(__name__)
    return logging.getLogger(module.__name__)

def get_class_logger(cls: Type) -> logging.Logger:
    """Get a logger instance for a class.
    
    This function should be used in class constructors to get a logger
    that uses the class's module and name.
    
    Args:
        cls: The class to get a logger for
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(f"{cls.__module__}.{cls.__name__}")

def setup_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """Set up logging configuration based on the provided config.
    
    Args:
        config: Dictionary containing logging configuration. If None, default configuration is used.
    """
    # Default configuration
    default_config = {
        'level': 'INFO',
        'format': '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        'date_format': '%Y-%m-%d %H:%M:%S',
        'handlers': {
            'console': {
                'enabled': True,
                'level': 'INFO'
            },
            'file': {
                'enabled': True,
                'level': 'INFO',
                'filename': 'quant_estate_{date}.log',
                'date_format': '%Y-%m-%d',
                'directory': 'logs'
            }
        }
    }
    
    # Merge provided config with defaults
    if config:
        log_config = config.get('logging', {})
        default_config.update(log_config)
    log_config = default_config
    
    # Get logging settings
    log_level = getattr(logging, log_config.get('level', 'INFO').upper())
    log_format = log_config.get('format', '%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    date_format = log_config.get('date_format', '%Y-%m-%d %H:%M:%S')
    
    # Create formatter
    formatter = logging.Formatter(log_format, date_format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler if enabled
    if log_config.get('handlers', {}).get('console', {}).get('enabled', True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, 
            log_config['handlers']['console'].get('level', 'INFO').upper()))
        root_logger.addHandler(console_handler)
    
    # Add file handler if enabled
    file_config = log_config.get('handlers', {}).get('file', {})
    if file_config.get('enabled', True):
        # Create logs directory
        project_root = Path(__file__).parent.parent
        logs_dir = project_root / file_config.get('directory', 'logs')
        logs_dir.mkdir(exist_ok=True)
        
        # Create log file with date
        date_str = datetime.now().strftime(file_config.get('date_format', '%Y-%m-%d'))
        filename = file_config.get('filename', 'quant_estate_{date}.log').format(date=date_str)
        log_file = logs_dir / filename
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, 
            file_config.get('level', 'DEBUG').upper()))
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.
    
    This function should only be used when you need a specific logger name
    that doesn't match the module or class structure. For module-level logging,
    use get_module_logger() instead. For class-level logging, use get_class_logger().
    
    Args:
        name: Name of the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name) 