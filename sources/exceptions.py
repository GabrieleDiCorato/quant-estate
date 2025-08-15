"""
Project-wide exception hierarchy used by scrapers and storage layers.
"""


class ConnectorError(Exception):
    """Base exception for all connector-related errors."""

    pass


class ScrapingError(ConnectorError):
    """Base exception for all scraping-related errors."""

    pass


class StorageError(ConnectorError):
    """Base exception for all storage-related errors."""

    pass


class ConfigurationError(ConnectorError):
    """Base exception for all configuration-related errors."""

    pass


class ValidationError(ConnectorError):
    """Base exception for all validation-related errors."""

    pass


# Connector-specific exceptions
class ImmobiliareError(ConnectorError):
    """Base exception for Immobiliare.it specific errors."""

    pass


class InvalidURLError(ValidationError, ImmobiliareError):
    """Raised when the URL is invalid for immobiliare.it."""

    pass


class RequestError(ScrapingError, ImmobiliareError):
    """Raised when there's an error making a request to immobiliare.it."""

    pass


class DataExtractionError(ScrapingError, ImmobiliareError):
    """Raised when there's an error extracting data from the response."""

    pass
