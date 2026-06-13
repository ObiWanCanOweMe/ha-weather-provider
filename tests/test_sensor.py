"""Tests for optional HA Weather Provider sensor entities."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import EntityCategory, UnitOfSpeed

from custom_components.ha_weather_provider.const import (
    CONF_EXTRA_ENTITIES,
    CONF_UNITS,
    DOMAIN,
    INTEGRATION_VERSION,
)
from custom_components.ha_weather_provider.coordinator import TWCWeatherData
from custom_components.ha_weather_provider.sensor import (
    TWCSensorEntity,
    async_setup_entry,
)


def _coordinator() -> SimpleNamespace:
    """Return coordinator-shaped test data for sensor entities."""
    return SimpleNamespace(
        data=TWCWeatherData(
            current={
                "wxPhraseLong": "Partly Cloudy",
                "validTimeUtc": 1718121600,
                "windGust": 12,
            },
            daily_forecast={"validTimeUtc": []},
            hourly_forecast={"validTimeUtc": []},
            alert_headlines={
                "alerts": [
                    {"headlineText": "Severe Thunderstorm Warning"},
                    {"headlineText": "Flood Watch"},
                ]
            },
        )
    )


def _entry(*, options: dict[str, object] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        entry_id="entry-id",
        data={CONF_UNITS: "e"},
        options=options or {},
    )


async def test_sensor_setup_skips_entities_when_option_disabled(hass) -> None:
    """Optional sensors should not be created unless the config option is enabled."""
    async_add_entities = Mock()
    entry = _entry(options={CONF_EXTRA_ENTITIES: False})
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _coordinator()

    await async_setup_entry(hass, entry, async_add_entities)

    async_add_entities.assert_not_called()


async def test_sensor_setup_adds_optional_entities_when_enabled(hass) -> None:
    """The first optional milestone should expose a compact diagnostic sensor set."""
    async_add_entities = Mock()
    entry = _entry(options={CONF_EXTRA_ENTITIES: True})
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _coordinator()

    await async_setup_entry(hass, entry, async_add_entities)

    entities = async_add_entities.call_args.args[0]
    assert [entity.unique_id for entity in entities] == [
        "entry-id_alert_count",
        "entry-id_condition_phrase",
        "entry-id_observation_time",
        "entry-id_integration_version",
        "entry-id_wind_gust",
    ]


def test_optional_sensor_values() -> None:
    """Optional sensors should map values from coordinator data without API calls."""
    coordinator = _coordinator()
    entry = _entry(options={CONF_EXTRA_ENTITIES: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.entity_descriptions()
        ]
    }

    assert entities["alert_count"].native_value == 2
    assert entities["condition_phrase"].native_value == "Partly Cloudy"
    assert entities["observation_time"].native_value == datetime(
        2024, 6, 11, 16, 0, tzinfo=UTC
    )
    assert entities["integration_version"].native_value == INTEGRATION_VERSION
    assert entities["wind_gust"].native_value == 12
    assert entities["wind_gust"].native_unit_of_measurement == UnitOfSpeed.MILES_PER_HOUR
    assert entities["observation_time"].device_class == SensorDeviceClass.TIMESTAMP
    assert entities["integration_version"].entity_category == EntityCategory.DIAGNOSTIC


def test_optional_sensor_handles_missing_wind_gust() -> None:
    """Missing TWC gust values should stay unavailable rather than falling back."""
    coordinator = _coordinator()
    coordinator.data.current["windGust"] = None
    entry = _entry(options={CONF_EXTRA_ENTITIES: True})
    entity = next(
        entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.entity_descriptions()
        ]
        if entity.entity_description.key == "wind_gust"
    )

    assert entity.native_value is None
