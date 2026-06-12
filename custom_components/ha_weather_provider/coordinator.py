"""Data coordinator for HA Weather Provider."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import TWCClient, TWCError
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class TWCWeatherData:
    """Combined TWC weather payloads."""

    current: dict[str, Any]
    daily_forecast: dict[str, Any]


class TWCWeatherCoordinator(DataUpdateCoordinator[TWCWeatherData]):
    """Coordinate TWC weather data refreshes."""

    def __init__(self, hass: HomeAssistant, client: TWCClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_UPDATE_INTERVAL,
            always_update=False,
        )
        self.client = client

    async def _async_update_data(self) -> TWCWeatherData:
        """Fetch current conditions and 7-day daily forecast."""
        try:
            current = await self.client.async_get_current_conditions()
            daily_forecast = await self.client.async_get_daily_forecast()
        except TWCError as err:
            raise UpdateFailed(str(err)) from err

        return TWCWeatherData(current=current, daily_forecast=daily_forecast)
