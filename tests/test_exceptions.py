"""
Exhaustive tests for exception classes.
"""

from kovamind import (
    KovaMindError,
    AuthError,
    RateLimitError,
    NotFoundError,
    ServerError,
)


def test_kovamind_error_message_and_status():
    e = KovaMindError("something broke", status_code=418)
    assert str(e) == "something broke"
    assert e.status_code == 418


def test_kovamind_error_no_status():
    e = KovaMindError("oops")
    assert e.status_code is None


def test_auth_error_defaults():
    e = AuthError()
    assert e.status_code == 401
    assert "Invalid or missing API key" in str(e)


def test_auth_error_custom_message():
    e = AuthError("Token expired")
    assert str(e) == "Token expired"
    assert e.status_code == 401


def test_rate_limit_error_retry_after():
    e = RateLimitError(retry_after=60)
    assert e.status_code == 429
    assert e.retry_after == 60


def test_rate_limit_error_no_retry_after():
    e = RateLimitError()
    assert e.retry_after is None


def test_not_found_error_custom_message():
    e = NotFoundError("Pattern 42 not found")
    assert str(e) == "Pattern 42 not found"
    assert e.status_code == 404


def test_not_found_error_defaults():
    e = NotFoundError()
    assert e.status_code == 404


def test_server_error_custom_status():
    e = ServerError(status_code=503)
    assert e.status_code == 503


def test_server_error_defaults():
    e = ServerError()
    assert e.status_code == 500


def test_exception_hierarchy():
    assert issubclass(AuthError, KovaMindError)
    assert issubclass(RateLimitError, KovaMindError)
    assert issubclass(NotFoundError, KovaMindError)
    assert issubclass(ServerError, KovaMindError)
    assert issubclass(KovaMindError, Exception)
