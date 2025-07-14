"""
Simple Logger base class for inheritance.
"""

from .logging_utils import get_class_logger

class LoggingMixin:
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
        self._logger = None

    @property
    def logger(self):
        """Lazy-loaded logger property."""
        if self._logger is None:
            self._logger = get_class_logger(self.__class__)
        return self._logger
