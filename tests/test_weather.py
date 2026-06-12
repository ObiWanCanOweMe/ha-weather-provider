"""Tests for the HA Weather Provider weather platform."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from custom_components.ha_weather_provider.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
)
from custom_components.ha_weather_provider.weather import async_setup_entry


async def test_async_setup_entry_uses_coordinates_for_display_name():
    """Weather setup should build the display location from coordinates."""
    async_add_entities = Mock()
    entry = SimpleNamespace(
        data={
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
        }
    )

    await async_setup_entry(None, entry, async_add_entities)

    entity = async_add_entities.call_args.args[0][0]
    assert entity._attr_name == "Weather Provider 40.5800,-111.6600"
