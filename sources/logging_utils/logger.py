"""
Simple Logger base class for inheritance.
"""

from __future__ import annotations

import logging as stdlib_logging
from typing import Type

class Logger:
    """Simple base class that provides logging capability to subclasses.
    
    Usage:
        1. First, configure logging at application startup:
           from sources.logging.logging_utils import setup_logging
           setup_logging()
        
        2. Then inherit from Logger in your classes:
           class MyClass(Logger):
               def __init__(self):
                   super().__init__()
                   self.logger.info("MyClass initialized")
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """Initialize the logger for this class.
        
        Note: Logging must be configured at application startup using
        setup_logging() from logging_utils before using this class.
        """
        super().__init__(*args, **kwargs)
        self.logger = self._get_class_logger()
    
    def _get_class_logger(self) -> stdlib_logging.Logger:
        """Get a logger instance for this class.
        
        Returns:
            stdlib_logging.Logger: Logger instance named after the class
        """
        return stdlib_logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
