"""Tests for the standalone TWC client package exports."""

from twc_weather_client import (
    TWCAuthError,
    TWCError,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)


def test_twc_client_exports_errors() -> None:
    """The standalone package exposes all public TWC exceptions."""
    assert issubclass(TWCAuthError, TWCError)
    assert issubclass(TWCNoDataError, TWCError)
    assert issubclass(TWCPermissionError, TWCError)
    assert issubclass(TWCRequestError, TWCError)
