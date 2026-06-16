"""Async client for The Weather Company API."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
from aiohttp import ClientSession

from .twc_weather_client import (
    TWCAuthError,
    TWCError,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)

from .const import (
    DEFAULT_AIR_QUALITY_SCALE,
    DEFAULT_DAILY_FORECAST_DURATION,
    DEFAULT_HOURLY_FORECAST_DURATION,
    DEFAULT_POLLEN_FORECAST_DURATION,
)

BASE_URL = "https://api.weather.com"
CURRENT_PATH = "/v3/wx/observations/current"
DAILY_FORECAST_PATH_PREFIX = "/v3/wx/forecast/daily"
HOURLY_FORECAST_PATH_PREFIX = "/v3/wx/forecast/hourly"
DAILY_FORECAST_PATH = f"{DAILY_FORECAST_PATH_PREFIX}/{DEFAULT_DAILY_FORECAST_DURATION}"
HOURLY_FORECAST_PATH = f"{HOURLY_FORECAST_PATH_PREFIX}/{DEFAULT_HOURLY_FORECAST_DURATION}"
ALERT_HEADLINES_PATH = "/v3/alerts/headlines"
POLLEN_FORECAST_PATH_PREFIX = "/v2/indices/pollen/daypart"
POLLEN_FORECAST_PATH = f"{POLLEN_FORECAST_PATH_PREFIX}/{DEFAULT_POLLEN_FORECAST_DURATION}"
POLLEN_OBSERVATION_PATH = (
    "/v1/geocode/{latitude}/{longitude}/observations/pollen.json"
)
TROPICAL_CURRENT_POSITION_PATH = "/v2/tropical/currentposition"
AIR_QUALITY_PATH = "/v3/wx/globalAirQuality"


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
        daily_forecast_duration: str = DEFAULT_DAILY_FORECAST_DURATION,
        hourly_forecast_duration: str = DEFAULT_HOURLY_FORECAST_DURATION,
    ) -> None:
        self._session = session
        self._api_key = api_key
        self._latitude = latitude
        self._longitude = longitude
        self._units = units
        self._language = language
        self._daily_forecast_duration = daily_forecast_duration
        self._hourly_forecast_duration = hourly_forecast_duration

    @property
    def _weather_query_params(self) -> dict[str, str]:
        return {
            "apiKey": self._api_key,
            "geocode": f"{self._latitude},{self._longitude}",
            "units": self._units,
            "language": self._language,
            "format": "json",
        }

    @property
    def _alert_query_params(self) -> dict[str, str]:
        return {
            "apiKey": self._api_key,
            "geocode": f"{self._latitude},{self._longitude}",
            "language": self._language,
            "format": "json",
        }

    @property
    def _pollen_query_params(self) -> dict[str, str]:
        return self._alert_query_params

    @property
    def _pollen_observation_query_params(self) -> dict[str, str]:
        return {
            "apiKey": self._api_key,
            "language": self._language,
        }

    @property
    def _tropical_query_params(self) -> dict[str, str]:
        return {
            "apiKey": self._api_key,
            "source": "default",
            "basin": "all",
            "language": self._language,
            "format": "json",
            "units": self._units,
            "nautical": "false",
        }

    @property
    def _air_quality_query_params(self) -> dict[str, str]:
        return {
            "apiKey": self._api_key,
            "geocode": f"{self._latitude},{self._longitude}",
            "language": self._language,
            "scale": DEFAULT_AIR_QUALITY_SCALE,
            "format": "json",
        }

    async def async_get_current_conditions(self) -> dict[str, Any]:
        """Return current conditions."""
        return await self._async_get_json(CURRENT_PATH, params=self._weather_query_params)

    async def async_get_daily_forecast(self) -> dict[str, Any]:
        """Return daily forecast data."""
        return await self._async_get_json(
            f"{DAILY_FORECAST_PATH_PREFIX}/{self._daily_forecast_duration}",
            params=self._weather_query_params,
        )

    async def async_get_hourly_forecast(self) -> dict[str, Any]:
        """Return hourly forecast data."""
        return await self._async_get_json(
            f"{HOURLY_FORECAST_PATH_PREFIX}/{self._hourly_forecast_duration}",
            params=self._weather_query_params,
        )

    async def async_get_alert_headlines(self) -> dict[str, Any]:
        """Return active weather alert headlines."""
        try:
            return await self._async_get_json(
                ALERT_HEADLINES_PATH,
                params=self._alert_query_params,
                no_data_statuses={404},
            )
        except TWCNoDataError:
            return {"alerts": []}

    async def async_get_pollen_forecast(self) -> dict[str, Any]:
        """Return pollen forecast data, when the endpoint is available."""
        try:
            return await self._async_get_json(
                POLLEN_FORECAST_PATH, params=self._pollen_query_params
            )
        except (TWCNoDataError, TWCPermissionError):
            return {}

    async def async_get_pollen_observation(self) -> dict[str, Any]:
        """Return U.S. pollen observation data, when the endpoint is available."""
        try:
            return await self._async_get_json(
                POLLEN_OBSERVATION_PATH.format(
                    latitude=self._latitude,
                    longitude=self._longitude,
                ),
                params=self._pollen_observation_query_params,
            )
        except (TWCAuthError, TWCNoDataError, TWCPermissionError):
            return {}

    async def async_get_tropical_current_position(self) -> dict[str, Any]:
        """Return active tropical storm current-position data, when available."""
        try:
            return await self._async_get_json(
                TROPICAL_CURRENT_POSITION_PATH, params=self._tropical_query_params
            )
        except (TWCAuthError, TWCNoDataError, TWCPermissionError):
            return {}

    async def async_get_air_quality(self) -> dict[str, Any]:
        """Return global air quality data, when the endpoint is available."""
        try:
            return await self._async_get_json(
                AIR_QUALITY_PATH, params=self._air_quality_query_params
            )
        except (TWCAuthError, TWCNoDataError, TWCPermissionError):
            return {}

    async def _async_get_json(
        self,
        path: str,
        *,
        params: dict[str, str],
        no_data_statuses: set[int] | None = None,
    ) -> dict[str, Any]:
        url = f"{BASE_URL}{path}"
        try:
            async with self._session.get(
                url,
                params=params,
                headers={"Accept-Encoding": "gzip"},
            ) as response:
                if no_data_statuses and response.status in no_data_statuses:
                    raise TWCNoDataError("TWC returned no data")
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
