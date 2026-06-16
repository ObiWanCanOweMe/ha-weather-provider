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
