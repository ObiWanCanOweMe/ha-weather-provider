"""The HA Weather Provider integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TWCClient
from .const import (
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_UNITS,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    UPDATE_INTERVAL_MINUTES,
)
from .coordinator import TWCWeatherCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["weather", "sensor"]
REQUIRED_ENTRY_KEYS = (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_UNITS,
    CONF_LANGUAGE,
)


def _entry_update_interval(entry: ConfigEntry) -> timedelta:
    """Return the configured coordinator update interval."""
    options = getattr(entry, "options", {})
    minutes = options.get(
        CONF_UPDATE_INTERVAL_MINUTES,
        DEFAULT_UPDATE_INTERVAL_MINUTES,
    )
    if minutes not in UPDATE_INTERVAL_MINUTES:
        minutes = DEFAULT_UPDATE_INTERVAL_MINUTES
    return timedelta(minutes=minutes)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate legacy config entries."""
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
    session = async_get_clientsession(hass)
    client = TWCClient(
        session=session,
        api_key=entry.data[CONF_API_KEY],
        latitude=entry.data[CONF_LATITUDE],
        longitude=entry.data[CONF_LONGITUDE],
        units=entry.data[CONF_UNITS],
        language=entry.data[CONF_LANGUAGE],
    )
    coordinator = TWCWeatherCoordinator(
        hass,
        client,
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
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
