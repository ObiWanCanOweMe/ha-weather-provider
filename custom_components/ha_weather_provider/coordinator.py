"""Data coordinator for HA Weather Provider."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    TWCAuthError,
    TWCClient,
    TWCError,
    TWCNoDataError,
    TWCPermissionError,
)
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class TWCWeatherData:
    """Combined TWC weather payloads."""

    current: dict[str, Any]
    daily_forecast: dict[str, Any]
    hourly_forecast: dict[str, Any]
    alert_headlines: dict[str, Any]
    pollen_forecast: dict[str, Any] = field(default_factory=dict)
    tropical_current_position: dict[str, Any] = field(default_factory=dict)


class TWCWeatherCoordinator(DataUpdateCoordinator[TWCWeatherData]):
    """Coordinate TWC weather data refreshes."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TWCClient,
        *,
        pollen_enabled: bool = False,
        tropical_enabled: bool = False,
        update_interval: timedelta = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
            always_update=False,
        )
        self.client = client
        self.pollen_enabled = pollen_enabled
        self.tropical_enabled = tropical_enabled

    async def _async_update_data(self) -> TWCWeatherData:
        """Fetch current conditions and 7-day daily forecast."""
        try:
            current = await self.client.async_get_current_conditions()
            daily_forecast = await self.client.async_get_daily_forecast()
            hourly_forecast = await self.client.async_get_hourly_forecast()
            alert_headlines = await self.client.async_get_alert_headlines()
        except (TWCAuthError, TWCPermissionError) as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except TWCError as err:
            raise UpdateFailed(str(err)) from err

        pollen_forecast: dict[str, Any] = {}
        if self.pollen_enabled:
            try:
                pollen_forecast = await self.client.async_get_pollen_forecast()
            except (TWCAuthError, TWCNoDataError, TWCPermissionError):
                _LOGGER.debug("Optional TWC pollen forecast endpoint is unavailable")
            except TWCError as err:
                raise UpdateFailed(str(err)) from err

        tropical_current_position: dict[str, Any] = {}
        if self.tropical_enabled:
            try:
                tropical_current_position = (
                    await self.client.async_get_tropical_current_position()
                )
            except TWCError:
                _LOGGER.debug(
                    "Optional TWC tropical current-position endpoint is unavailable"
                )

        return TWCWeatherData(
            current=current,
            daily_forecast=daily_forecast,
            hourly_forecast=hourly_forecast,
            alert_headlines=alert_headlines,
            pollen_forecast=pollen_forecast,
            tropical_current_position=tropical_current_position,
        )
