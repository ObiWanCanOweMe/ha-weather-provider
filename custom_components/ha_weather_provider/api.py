"""Async client for The Weather Company API."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
from aiohttp import ClientSession

BASE_URL = "https://api.weather.com"
CURRENT_PATH = "/v3/wx/observations/current"
DAILY_FORECAST_PATH = "/v3/wx/forecast/daily/7day"
HOURLY_FORECAST_PATH = "/v3/wx/forecast/hourly/2day"


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
    """Async client for The Weather Company API."""

    def __init__(
        self,
        *,
        session: ClientSession,
        api_key: str,
        latitude: float,
        longitude: float,
        units: str,
        language: str,
    ) -> None:
        self._session = session
        self._api_key = api_key
        self._latitude = latitude
        self._longitude = longitude
        self._units = units
        self._language = language

    @property
    def _query_params(self) -> dict[str, str]:
        return {
            "apiKey": self._api_key,
            "geocode": f"{self._latitude},{self._longitude}",
            "units": self._units,
            "language": self._language,
            "format": "json",
        }

    async def async_get_current_conditions(self) -> dict[str, Any]:
        """Return current conditions."""
        return await self._async_get_json(CURRENT_PATH)

    async def async_get_daily_forecast(self) -> dict[str, Any]:
        """Return daily forecast data."""
        return await self._async_get_json(DAILY_FORECAST_PATH)

    async def async_get_hourly_forecast(self) -> dict[str, Any]:
        """Return hourly forecast data."""
        return await self._async_get_json(HOURLY_FORECAST_PATH)

    async def _async_get_json(self, path: str) -> dict[str, Any]:
        url = f"{BASE_URL}{path}"
        try:
            async with self._session.get(
                url,
                params=self._query_params,
                headers={"Accept-Encoding": "gzip"},
            ) as response:
                self._raise_for_status(response.status)
                payload = await response.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise TWCRequestError("TWC request failed") from err
        except (TypeError, ValueError) as err:
            raise TWCRequestError("TWC response body was not valid JSON") from err

        if not isinstance(payload, dict):
            raise TWCRequestError("TWC response body was not a JSON object")

        return payload

    def _raise_for_status(self, status: int) -> None:
        if status == 200:
            return
        if status == 204:
            raise TWCNoDataError("TWC returned no data")
        if status == 401:
            raise TWCAuthError("TWC rejected the configured API key")
        if status == 403:
            raise TWCPermissionError("TWC API key does not have access")
        if status in {400, 404, 405, 406, 408, 500, 502, 503, 504}:
            raise TWCRequestError(f"TWC request failed with status {status}")
        raise TWCRequestError(f"TWC request failed with unexpected status {status}")
