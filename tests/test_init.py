"""Tests for HA Weather Provider integration setup and migration."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_weather_provider import async_migrate_entry, async_setup_entry, async_unload_entry
from custom_components.ha_weather_provider.const import (
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_UNITS,
    DOMAIN,
)


async def test_async_migrate_entry_rejects_legacy_location_only_entry(hass, caplog):
    """Legacy entries without client fields should fail migration cleanly."""
    entry = SimpleNamespace(
        entry_id="legacy-entry",
        data={"location": "Salt Lake City"},
    )

    with caplog.at_level("ERROR"):
        result = await async_migrate_entry(hass, entry)

    assert result is False
    assert "missing required keys" in caplog.text
    assert DOMAIN in caplog.text


async def test_async_migrate_entry_updates_valid_entry_version(hass):
    """Valid entries should be marked as migrated to version 2."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="entry-id",
        version=1,
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
    )
    entry.add_to_hass(hass)

    result = await async_migrate_entry(hass, entry)

    assert result is True
    assert entry.version == 2


@pytest.mark.asyncio
async def test_async_setup_entry_cleans_up_on_forward_failure(hass):
    """Stored coordinator should be removed if platform forwarding fails."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "custom_components.ha_weather_provider.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.TWCClient", return_value=object()
    ) as mock_client, patch(
        "custom_components.ha_weather_provider.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(RuntimeError, match="boom"):
            await async_setup_entry(hass, entry)

    assert hass.data.get(DOMAIN, {}).get(entry.entry_id) is None
    mock_client.assert_called_once()
    mock_coordinator.assert_called_once()


@pytest.mark.asyncio
async def test_async_setup_entry_uses_configured_update_interval(hass):
    """Setup should pass the selected update interval into the coordinator."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={CONF_UPDATE_INTERVAL_MINUTES: 60},
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "custom_components.ha_weather_provider.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.TWCClient", return_value=object()
    ), patch(
        "custom_components.ha_weather_provider.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_coordinator.call_args.kwargs["update_interval"] == timedelta(minutes=60)


@pytest.mark.asyncio
async def test_async_unload_entry_removes_stored_coordinator(hass):
    """Successful unload should remove the cached coordinator."""
    entry = SimpleNamespace(entry_id="entry-id")
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = object()

    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=True
    ) as mock_unload:
        result = await async_unload_entry(hass, entry)

    assert result is True
    assert entry.entry_id not in hass.data.get(DOMAIN, {})
    mock_unload.assert_called_once()
