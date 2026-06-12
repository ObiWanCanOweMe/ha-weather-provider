"""Weather platform for HA Weather Provider."""

from __future__ import annotations

from homeassistant.components.weather import WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TWCWeatherCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the weather entity from a config entry."""
    coordinator: TWCWeatherCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HAWeatherProviderEntity(coordinator, entry)])


class HAWeatherProviderEntity(CoordinatorEntity[TWCWeatherCoordinator], WeatherEntity):
    """Representation of a weather entity."""

    def __init__(self, coordinator: TWCWeatherCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = entry.title
        self._attr_unique_id = entry.entry_id
