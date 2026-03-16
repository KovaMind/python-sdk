"""
kovamind.exceptions -- Error hierarchy for the Kova Mind SDK.
"""


class KovaMindError(Exception):
    """Base exception for all Kova Mind errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AuthError(KovaMindError):
    """Raised when the API key is missing, invalid, or revoked (HTTP 401)."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, status_code=401)


class RateLimitError(KovaMindError):
    """Raised when the rate limit is exceeded (HTTP 429)."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class NotFoundError(KovaMindError):
    """Raised when a requested resource is not found (HTTP 404)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ServerError(KovaMindError):
    """Raised on unexpected server errors (HTTP 5xx)."""

    def __init__(self, message: str = "Internal server error", status_code: int = 500):
        super().__init__(message, status_code=status_code)
