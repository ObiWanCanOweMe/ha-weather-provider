"""The HA Weather Provider integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["weather", "sensor"]
REQUIRED_ENTRY_KEYS = (
    "api_key",
    "latitude",
    "longitude",
    "units",
    "language",
)


def _entry_update_interval(entry: ConfigEntry) -> timedelta:
    """Return the configured coordinator update interval."""
    from .const import (
        CONF_UPDATE_INTERVAL_MINUTES,
        DEFAULT_UPDATE_INTERVAL_MINUTES,
        UPDATE_INTERVAL_MINUTES,
    )

    options = getattr(entry, "options", {})
    minutes = options.get(
        CONF_UPDATE_INTERVAL_MINUTES,
        DEFAULT_UPDATE_INTERVAL_MINUTES,
    )
    if minutes not in UPDATE_INTERVAL_MINUTES:
        minutes = DEFAULT_UPDATE_INTERVAL_MINUTES
    return timedelta(minutes=minutes)


def _entry_forecast_duration(
    entry: ConfigEntry,
    option_key: str,
    allowed_values: tuple[str, ...],
    default_value: str,
) -> str:
    """Return a supported configured forecast duration."""
    options = getattr(entry, "options", {})
    duration = options.get(option_key, default_value)
    if duration not in allowed_values:
        duration = default_value
    return duration


def _entry_enable_pollen(entry: ConfigEntry) -> bool:
    """Return whether optional pollen data is enabled."""
    from .const import CONF_ENABLE_POLLEN

    options = getattr(entry, "options", {})
    return options.get(CONF_ENABLE_POLLEN) is True


def _entry_enable_tropical_weather(entry: ConfigEntry) -> bool:
    """Return whether optional tropical weather data is enabled."""
    from .const import CONF_ENABLE_TROPICAL_WEATHER

    options = getattr(entry, "options", {})
    return options.get(CONF_ENABLE_TROPICAL_WEATHER) is True


def _entry_enable_air_quality(entry: ConfigEntry) -> bool:
    """Return whether optional air quality data is enabled."""
    from .const import CONF_ENABLE_AIR_QUALITY

    options = getattr(entry, "options", {})
    return options.get(CONF_ENABLE_AIR_QUALITY) is True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate legacy config entries."""
    from .const import DOMAIN

    missing_keys = [key for key in REQUIRED_ENTRY_KEYS if key not in entry.data]
    if missing_keys:
        _LOGGER.error(
            "Cannot migrate config entry %s for %s: missing required keys %s",
            entry.entry_id,
            DOMAIN,
            ", ".join(missing_keys),
        )
        return False

    hass.config_entries.async_update_entry(entry, version=2)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Weather Provider from a config entry."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from .const import (
        CONF_API_KEY,
        CONF_DAILY_FORECAST_DURATION,
        CONF_HOURLY_FORECAST_DURATION,
        CONF_LANGUAGE,
        CONF_LATITUDE,
        CONF_LONGITUDE,
        CONF_UNITS,
        DAILY_FORECAST_DURATIONS,
        DEFAULT_DAILY_FORECAST_DURATION,
        DEFAULT_HOURLY_FORECAST_DURATION,
        DOMAIN,
        HOURLY_FORECAST_DURATIONS,
    )
    from .coordinator import TWCWeatherCoordinator
    from .twc_weather_client import TWCClient

    session = async_get_clientsession(hass)
    client = TWCClient(
        session=session,
        api_key=entry.data[CONF_API_KEY],
        latitude=entry.data[CONF_LATITUDE],
        longitude=entry.data[CONF_LONGITUDE],
        units=entry.data[CONF_UNITS],
        language=entry.data[CONF_LANGUAGE],
        daily_forecast_duration=_entry_forecast_duration(
            entry,
            CONF_DAILY_FORECAST_DURATION,
            DAILY_FORECAST_DURATIONS,
            DEFAULT_DAILY_FORECAST_DURATION,
        ),
        hourly_forecast_duration=_entry_forecast_duration(
            entry,
            CONF_HOURLY_FORECAST_DURATION,
            HOURLY_FORECAST_DURATIONS,
            DEFAULT_HOURLY_FORECAST_DURATION,
        ),
    )
    coordinator = TWCWeatherCoordinator(
        hass,
        client,
        pollen_enabled=_entry_enable_pollen(entry),
        tropical_enabled=_entry_enable_tropical_weather(entry),
        air_quality_enabled=_entry_enable_air_quality(entry),
        config_entry=entry,
        update_interval=_entry_update_interval(entry),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    from .const import DOMAIN

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
