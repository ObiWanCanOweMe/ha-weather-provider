"""Tests for the HA Weather Provider weather platform."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from custom_components.ha_weather_provider.const import DOMAIN
from custom_components.ha_weather_provider.weather import async_setup_entry


async def test_async_setup_entry_uses_coordinator_from_hass_data(hass):
    """Weather setup should read the stored coordinator and add one entity."""
    async_add_entities = Mock()
    coordinator = object()
    entry = SimpleNamespace(
        title="TWC Weather 40.5800,-111.6600",
        entry_id="abc123",
        data={},
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await async_setup_entry(hass, entry, async_add_entities)

    entity = async_add_entities.call_args.args[0][0]
    assert entity.coordinator is coordinator
    assert entity._attr_name == entry.title
    assert entity._attr_unique_id == entry.entry_id
