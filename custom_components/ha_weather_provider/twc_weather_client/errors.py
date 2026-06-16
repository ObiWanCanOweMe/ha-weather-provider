"""Errors raised by the The Weather Company client package."""

from __future__ import annotations


class TWCError(Exception):
    """Base error for TWC client failures."""


class TWCAuthError(TWCError):
    """TWC rejected the configured API key."""


class TWCPermissionError(TWCError):
    """TWC API key does not have access to the requested endpoint."""


class TWCNoDataError(TWCError):
    """TWC returned no data for the request."""


class TWCRequestError(TWCError):
    """TWC request failed."""


def is_optional_endpoint_unavailable(error: Exception) -> bool:
    """Return whether an optional endpoint failure should be treated as unavailable."""
    return isinstance(error, (TWCAuthError, TWCNoDataError, TWCPermissionError))
