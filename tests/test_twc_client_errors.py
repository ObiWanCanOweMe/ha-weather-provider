"""Tests for the integration TWC client package exports."""

from custom_components.ha_weather_provider.twc_weather_client import (
    TWCAuthError,
    TWCError,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)


def test_twc_client_exports_errors() -> None:
    """The integration package exposes all public TWC exceptions."""
    assert issubclass(TWCAuthError, TWCError)
    assert issubclass(TWCNoDataError, TWCError)
    assert issubclass(TWCPermissionError, TWCError)
    assert issubclass(TWCRequestError, TWCError)
