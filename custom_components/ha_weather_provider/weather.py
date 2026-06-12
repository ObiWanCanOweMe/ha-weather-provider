"""Weather platform for HA Weather Provider."""

from __future__ import annotations

from homeassistant.components.weather import WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_LATITUDE, CONF_LONGITUDE


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the weather entity from a config entry."""
    if CONF_LATITUDE in entry.data and CONF_LONGITUDE in entry.data:
        location = f"{entry.data[CONF_LATITUDE]:.4f},{entry.data[CONF_LONGITUDE]:.4f}"
    else:
        location = str(entry.data.get("location", "Unknown"))
    async_add_entities([HAWeatherProviderEntity(location)])


class HAWeatherProviderEntity(WeatherEntity):
    """Representation of a weather entity."""

    def __init__(self, location: str) -> None:
        self._attr_name = f"Weather Provider {location}"
        self._attr_native_temperature_unit = None
        self._attr_native_temperature = None
        self._attr_native_humidity = None
        self._attr_native_pressure = None
        self._attr_native_wind_speed = None
        self._attr_condition = None

    @property
    def supported_features(self) -> int:
        return 0
