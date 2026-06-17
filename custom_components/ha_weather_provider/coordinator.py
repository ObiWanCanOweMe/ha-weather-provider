"""Data coordinator for HA Weather Provider."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
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

from .twc_weather_client import (
    TWCAuthError,
    TWCClient,
    TWCError,
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
    pollen_observation: dict[str, Any] = field(default_factory=dict)
    tropical_current_position: dict[str, Any] = field(default_factory=dict)
    air_quality: dict[str, Any] = field(default_factory=dict)


class TWCEndpointCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate refreshes for one TWC endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TWCClient,
        *,
        name: str,
        fetch_method: Callable[[], Awaitable[dict[str, Any]]],
        optional: bool = False,
        update_interval: timedelta = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the endpoint coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {name}",
            update_interval=update_interval,
            always_update=False,
        )
        self.client = client
        self.endpoint_name = name
        self._fetch_method = fetch_method
        self.optional = optional

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch endpoint data."""
        try:
            return await self._fetch_method()
        except (TWCAuthError, TWCPermissionError) as err:
            if self.optional:
                _LOGGER.debug(
                    "Optional TWC %s endpoint is unavailable: %s",
                    self.endpoint_name,
                    err,
                )
                return {}
            raise ConfigEntryAuthFailed(str(err)) from err
        except TWCError as err:
            if self.optional:
                _LOGGER.debug(
                    "Optional TWC %s endpoint update failed: %s",
                    self.endpoint_name,
                    err,
                )
                return {}
            raise UpdateFailed(str(err)) from err


class TWCObservationCoordinator(TWCEndpointCoordinator):
    """Coordinate TWC current condition refreshes."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TWCClient,
        *,
        update_interval: timedelta = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the observation coordinator."""
        super().__init__(
            hass,
            client,
            name="observation",
            fetch_method=client.async_get_current_conditions,
            update_interval=update_interval,
        )


class TWCDailyForecastCoordinator(TWCEndpointCoordinator):
    """Coordinate TWC daily forecast refreshes."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TWCClient,
        *,
        update_interval: timedelta = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the daily forecast coordinator."""
        super().__init__(
            hass,
            client,
            name="daily forecast",
            fetch_method=client.async_get_daily_forecast,
            update_interval=update_interval,
        )


class TWCHourlyForecastCoordinator(TWCEndpointCoordinator):
    """Coordinate TWC hourly forecast refreshes."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TWCClient,
        *,
        update_interval: timedelta = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the hourly forecast coordinator."""
        super().__init__(
            hass,
            client,
            name="hourly forecast",
            fetch_method=client.async_get_hourly_forecast,
            update_interval=update_interval,
        )


class TWCAlertCoordinator(TWCEndpointCoordinator):
    """Coordinate TWC alert headline refreshes."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TWCClient,
        *,
        update_interval: timedelta = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the alert coordinator."""
        super().__init__(
            hass,
            client,
            name="alert headlines",
            fetch_method=client.async_get_alert_headlines,
            update_interval=update_interval,
        )


class TWCPollenForecastCoordinator(TWCEndpointCoordinator):
    """Coordinate optional TWC pollen forecast refreshes."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TWCClient,
        *,
        update_interval: timedelta = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the pollen forecast coordinator."""
        super().__init__(
            hass,
            client,
            name="pollen forecast",
            fetch_method=client.async_get_pollen_forecast,
            optional=True,
            update_interval=update_interval,
        )


class TWCPollenObservationCoordinator(TWCEndpointCoordinator):
    """Coordinate optional TWC pollen observation refreshes."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TWCClient,
        *,
        update_interval: timedelta = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the pollen observation coordinator."""
        super().__init__(
            hass,
            client,
            name="pollen observation",
            fetch_method=client.async_get_pollen_observation,
            optional=True,
            update_interval=update_interval,
        )


class TWCTropicalCoordinator(TWCEndpointCoordinator):
    """Coordinate optional TWC tropical current-position refreshes."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TWCClient,
        *,
        update_interval: timedelta = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the tropical coordinator."""
        super().__init__(
            hass,
            client,
            name="tropical current position",
            fetch_method=client.async_get_tropical_current_position,
            optional=True,
            update_interval=update_interval,
        )


class TWCAirQualityCoordinator(TWCEndpointCoordinator):
    """Coordinate optional TWC air quality refreshes."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TWCClient,
        *,
        update_interval: timedelta = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the air quality coordinator."""
        super().__init__(
            hass,
            client,
            name="air quality",
            fetch_method=client.async_get_air_quality,
            optional=True,
            update_interval=update_interval,
        )


class TWCWeatherCoordinator(DataUpdateCoordinator[TWCWeatherData]):
    """Coordinate TWC weather data refreshes."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TWCClient,
        *,
        pollen_enabled: bool = False,
        tropical_enabled: bool = False,
        air_quality_enabled: bool = False,
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
        self.air_quality_enabled = air_quality_enabled
        self.observation_coordinator = TWCObservationCoordinator(
            hass,
            client,
            update_interval=update_interval,
        )
        self.daily_forecast_coordinator = TWCDailyForecastCoordinator(
            hass,
            client,
            update_interval=update_interval,
        )
        self.hourly_forecast_coordinator = TWCHourlyForecastCoordinator(
            hass,
            client,
            update_interval=update_interval,
        )
        self.alert_coordinator = TWCAlertCoordinator(
            hass,
            client,
            update_interval=update_interval,
        )
        self.pollen_forecast_coordinator = TWCPollenForecastCoordinator(
            hass,
            client,
            update_interval=update_interval,
        )
        self.pollen_observation_coordinator = TWCPollenObservationCoordinator(
            hass,
            client,
            update_interval=update_interval,
        )
        self.tropical_coordinator = TWCTropicalCoordinator(
            hass,
            client,
            update_interval=update_interval,
        )
        self.air_quality_coordinator = TWCAirQualityCoordinator(
            hass,
            client,
            update_interval=update_interval,
        )

    @property
    def endpoint_coordinators(self) -> dict[str, TWCEndpointCoordinator]:
        """Return endpoint-family coordinators by compatibility payload key."""
        return {
            "current": self.observation_coordinator,
            "daily_forecast": self.daily_forecast_coordinator,
            "hourly_forecast": self.hourly_forecast_coordinator,
            "alert_headlines": self.alert_coordinator,
            "pollen_forecast": self.pollen_forecast_coordinator,
            "pollen_observation": self.pollen_observation_coordinator,
            "tropical_current_position": self.tropical_coordinator,
            "air_quality": self.air_quality_coordinator,
        }

    async def _async_endpoint_data(
        self,
        coordinator: TWCEndpointCoordinator,
    ) -> dict[str, Any]:
        """Refresh one endpoint coordinator and preserve its current payload."""
        data = await coordinator._async_update_data()
        coordinator.async_set_updated_data(data)
        return data

    async def _async_update_data(self) -> TWCWeatherData:
        """Fetch enabled TWC endpoint families and combine compatibility data."""
        current = await self._async_endpoint_data(self.observation_coordinator)
        daily_forecast = await self._async_endpoint_data(
            self.daily_forecast_coordinator
        )
        hourly_forecast = await self._async_endpoint_data(
            self.hourly_forecast_coordinator
        )
        alert_headlines = await self._async_endpoint_data(self.alert_coordinator)

        pollen_forecast: dict[str, Any] = {}
        pollen_observation: dict[str, Any] = {}
        if self.pollen_enabled:
            pollen_forecast = await self._async_endpoint_data(
                self.pollen_forecast_coordinator
            )
            pollen_observation = await self._async_endpoint_data(
                self.pollen_observation_coordinator
            )

        tropical_current_position: dict[str, Any] = {}
        if self.tropical_enabled:
            tropical_current_position = await self._async_endpoint_data(
                self.tropical_coordinator
            )

        air_quality: dict[str, Any] = {}
        if self.air_quality_enabled:
            air_quality = await self._async_endpoint_data(
                self.air_quality_coordinator
            )

        return TWCWeatherData(
            current=current,
            daily_forecast=daily_forecast,
            hourly_forecast=hourly_forecast,
            alert_headlines=alert_headlines,
            pollen_forecast=pollen_forecast,
            pollen_observation=pollen_observation,
            tropical_current_position=tropical_current_position,
            air_quality=air_quality,
        )
