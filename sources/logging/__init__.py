"""
Logging package for the quant-estate project.
How to use it:

1. Import the `setup_logging` function from `sources.logging.logging`.
2. Call `setup_logging()` at the start of your application to configure logging.
3. Use `logging.getLogger(__name__)` to get a logger for your module. 
4. Log messages using the logger instance, e.g., `logger.info("message")`.
5. Optionally, you can pass a custom configuration file path to `setup_logging(config_path)`.
6. The logging configuration supports console and file handlers, with rotation based on time.

"""

from .logging_utils import (
    setup_logging, 
    get_logger, 
    get_class_logger, 
    is_logging_configured,
    reset_logging_configuration,
    LoggingConfigError,
)

__all__ = [
    'setup_logging', 
    'get_logger', 
    'get_class_logger', 
    'is_logging_configured',
    'reset_logging_configuration',
    'LoggingConfigError'
]
