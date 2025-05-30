class ImmobiliareError(Exception):
    """Base exception for all immobiliare-related errors."""
    pass

class InvalidURLError(ImmobiliareError):
    """Raised when the URL is invalid for immobiliare.it."""
    pass

class RequestError(ImmobiliareError):
    """Raised when there's an error making a request to immobiliare.it."""
    pass

class DataExtractionError(ImmobiliareError):
    """Raised when there's an error extracting data from the response."""
    pass

class StorageError(ImmobiliareError):
    """Raised when there's an error storing the data."""
    pass 