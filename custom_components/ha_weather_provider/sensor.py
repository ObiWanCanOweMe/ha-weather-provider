"""Optional sensor platform for HA Weather Provider."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_EXTRA_ENTITIES,
    CONF_UNITS,
    DISPLAY_NAME,
    DOMAIN,
    INTEGRATION_VERSION,
    UNIT_SYSTEMS,
)
from .coordinator import TWCWeatherCoordinator, TWCWeatherData


class TWCSensorEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Describes an optional TWC companion sensor."""

    value_fn: Callable[[TWCWeatherData], Any]
    unit_key: str | None = None


def _value(data: dict[str, Any], key: str) -> Any:
    """Return a non-null value from a TWC payload."""
    value = data.get(key)
    return None if value == "" else value


def _alert_count(data: TWCWeatherData) -> int:
    """Return the number of active alert headlines."""
    alerts = data.alert_headlines.get("alerts")
    return len(alerts) if isinstance(alerts, list) else 0


def _observation_time(data: TWCWeatherData) -> datetime | None:
    """Return the observation time as a timezone-aware datetime."""
    valid_time = _value(data.current, "validTimeUtc")
    if not isinstance(valid_time, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(valid_time, UTC)
    except (OverflowError, OSError, ValueError):
        return None


SENSOR_DESCRIPTIONS: tuple[TWCSensorEntityDescription, ...] = (
    TWCSensorEntityDescription(
        key="alert_count",
        name="Alert Count",
        icon="mdi:alert-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_alert_count,
    ),
    TWCSensorEntityDescription(
        key="condition_phrase",
        name="Condition Phrase",
        icon="mdi:weather-partly-cloudy",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _value(data.current, "wxPhraseLong"),
    ),
    TWCSensorEntityDescription(
        key="observation_time",
        name="Observation Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_observation_time,
    ),
    TWCSensorEntityDescription(
        key="integration_version",
        name="Integration Version",
        icon="mdi:package-variant-closed",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: INTEGRATION_VERSION,
    ),
    TWCSensorEntityDescription(
        key="wind_gust",
        name="Wind Gust",
        icon="mdi:weather-windy",
        value_fn=lambda data: _value(data.current, "windGust"),
        unit_key="speed",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up optional TWC companion sensors from a config entry."""
    if not entry.options.get(CONF_EXTRA_ENTITIES, False):
        return

    coordinator: TWCWeatherCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TWCSensorEntity(coordinator, entry, description)
            for description in SENSOR_DESCRIPTIONS
        ]
    )


class TWCSensorEntity(CoordinatorEntity[TWCWeatherCoordinator], SensorEntity):
    """Representation of an optional TWC companion sensor."""

    entity_description: TWCSensorEntityDescription

    def __init__(
        self,
        coordinator: TWCWeatherCoordinator,
        entry: ConfigEntry,
        description: TWCSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = description
        self._attr_name = f"{DISPLAY_NAME} {description.name}"
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._units = UNIT_SYSTEMS[entry.data[CONF_UNITS]]

    @staticmethod
    def entity_descriptions() -> tuple[TWCSensorEntityDescription, ...]:
        """Return optional TWC sensor descriptions."""
        return SENSOR_DESCRIPTIONS

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the sensor unit, when the value has one."""
        if self.entity_description.unit_key is None:
            return None
        return self._units[self.entity_description.unit_key]
