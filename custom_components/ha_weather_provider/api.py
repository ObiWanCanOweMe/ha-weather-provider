"""Temporary TWC API client shell."""

from __future__ import annotations

from typing import Any


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


class TWCClient:
    """Temporary TWC client shell; completed in the API client task."""

    def __init__(
        self,
        *,
        session: Any,
        api_key: str,
        latitude: float,
        longitude: float,
        units: str,
        language: str,
    ) -> None:
        self.session = session
        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.units = units
        self.language = language

    async def async_get_current_conditions(self) -> dict[str, Any]:
        """Return current conditions."""
        raise NotImplementedError
