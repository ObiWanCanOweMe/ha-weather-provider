"""Tests for HA Weather Provider integration setup and migration."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_weather_provider import (
    CONFIG_ENTRY_VERSION,
    async_migrate_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ha_weather_provider.const import (
    CONF_API_KEY,
    CONF_CURRENT_DETAIL_SENSORS,
    CONF_DAILY_FORECAST_DURATION,
    CONF_ENABLE_AIR_QUALITY,
    CONF_ENABLE_POLLEN,
    CONF_ENABLE_TROPICAL_WEATHER,
    CONF_EXTRA_ENTITIES,
    CONF_FORECAST_ADAPTER_SENSORS,
    CONF_HOURLY_FORECAST_DURATION,
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
    """Valid entries should be marked as migrated to the current version."""
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
    assert entry.version == CONFIG_ENTRY_VERSION
    assert entry.options[CONF_CURRENT_DETAIL_SENSORS] is False
    assert entry.options[CONF_FORECAST_ADAPTER_SENSORS] is False


async def test_async_migrate_entry_maps_legacy_extra_entities_option(hass):
    """Legacy extra_entities should migrate to both split sensor groups."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="entry-id",
        version=2,
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={CONF_EXTRA_ENTITIES: True, CONF_UPDATE_INTERVAL_MINUTES: 60},
    )
    entry.add_to_hass(hass)

    result = await async_migrate_entry(hass, entry)

    assert result is True
    assert entry.version == CONFIG_ENTRY_VERSION
    assert entry.options[CONF_EXTRA_ENTITIES] is True
    assert entry.options[CONF_CURRENT_DETAIL_SENSORS] is True
    assert entry.options[CONF_FORECAST_ADAPTER_SENSORS] is True
    assert entry.options[CONF_UPDATE_INTERVAL_MINUTES] == 60


async def test_async_migrate_entry_preserves_split_option_values(hass):
    """Migration should not override split options that already exist."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="entry-id",
        version=2,
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={
            CONF_EXTRA_ENTITIES: True,
            CONF_CURRENT_DETAIL_SENSORS: False,
        },
    )
    entry.add_to_hass(hass)

    result = await async_migrate_entry(hass, entry)

    assert result is True
    assert entry.version == CONFIG_ENTRY_VERSION
    assert entry.options[CONF_CURRENT_DETAIL_SENSORS] is False
    assert entry.options[CONF_FORECAST_ADAPTER_SENSORS] is True


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
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.twc_weather_client.TWCClient", return_value=object()
    ) as mock_client, patch(
        "custom_components.ha_weather_provider.coordinator.TWCWeatherCoordinator",
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
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.twc_weather_client.TWCClient", return_value=object()
    ), patch(
        "custom_components.ha_weather_provider.coordinator.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_coordinator.call_args.kwargs["update_interval"] == timedelta(minutes=60)
    assert mock_coordinator.call_args.kwargs["config_entry"] is entry


@pytest.mark.asyncio
async def test_async_setup_entry_passes_pollen_option_to_coordinator(hass):
    """Setup should pass the selected pollen option into the coordinator."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={CONF_ENABLE_POLLEN: True},
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.twc_weather_client.TWCClient", return_value=object()
    ), patch(
        "custom_components.ha_weather_provider.coordinator.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_coordinator.call_args.kwargs["pollen_enabled"] is True


@pytest.mark.asyncio
async def test_async_setup_entry_disables_pollen_by_default(hass):
    """Setup should leave pollen disabled unless explicitly enabled."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={},
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.twc_weather_client.TWCClient", return_value=object()
    ), patch(
        "custom_components.ha_weather_provider.coordinator.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_coordinator.call_args.kwargs["pollen_enabled"] is False


@pytest.mark.asyncio
async def test_async_setup_entry_passes_tropical_option_to_coordinator(hass):
    """Setup should pass the selected tropical weather option into the coordinator."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={CONF_ENABLE_TROPICAL_WEATHER: True},
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.twc_weather_client.TWCClient", return_value=object()
    ), patch(
        "custom_components.ha_weather_provider.coordinator.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_coordinator.call_args.kwargs["tropical_enabled"] is True


@pytest.mark.asyncio
async def test_async_setup_entry_disables_tropical_by_default(hass):
    """Setup should leave tropical weather disabled unless selected."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={},
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.twc_weather_client.TWCClient", return_value=object()
    ), patch(
        "custom_components.ha_weather_provider.coordinator.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_coordinator.call_args.kwargs["tropical_enabled"] is False


@pytest.mark.asyncio
async def test_async_setup_entry_requires_bool_true_for_tropical_option(hass):
    """Setup should not enable tropical weather for truthy non-bool values."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={CONF_ENABLE_TROPICAL_WEATHER: "true"},
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.twc_weather_client.TWCClient", return_value=object()
    ), patch(
        "custom_components.ha_weather_provider.coordinator.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_coordinator.call_args.kwargs["tropical_enabled"] is False


@pytest.mark.asyncio
async def test_async_setup_entry_passes_air_quality_option_to_coordinator(hass):
    """Setup should pass the selected air quality option into the coordinator."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={CONF_ENABLE_AIR_QUALITY: True},
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.twc_weather_client.TWCClient", return_value=object()
    ), patch(
        "custom_components.ha_weather_provider.coordinator.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_coordinator.call_args.kwargs["air_quality_enabled"] is True


@pytest.mark.asyncio
async def test_async_setup_entry_disables_air_quality_by_default(hass):
    """Setup should leave air quality disabled unless selected."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={},
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.twc_weather_client.TWCClient", return_value=object()
    ), patch(
        "custom_components.ha_weather_provider.coordinator.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_coordinator.call_args.kwargs["air_quality_enabled"] is False


@pytest.mark.asyncio
async def test_async_setup_entry_requires_bool_true_for_air_quality_option(hass):
    """Setup should not enable air quality for truthy non-bool values."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={CONF_ENABLE_AIR_QUALITY: "true"},
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.twc_weather_client.TWCClient", return_value=object()
    ), patch(
        "custom_components.ha_weather_provider.coordinator.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_coordinator.call_args.kwargs["air_quality_enabled"] is False


@pytest.mark.asyncio
async def test_async_setup_entry_passes_configured_forecast_durations(hass):
    """Setup should pass selected forecast durations into the TWC client."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={
            CONF_DAILY_FORECAST_DURATION: "15day",
            CONF_HOURLY_FORECAST_DURATION: "6hour",
        },
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.twc_weather_client.TWCClient", return_value=object()
    ) as mock_client, patch(
        "custom_components.ha_weather_provider.coordinator.TWCWeatherCoordinator",
        return_value=coordinator,
    ), patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_client.call_args.kwargs["daily_forecast_duration"] == "15day"
    assert mock_client.call_args.kwargs["hourly_forecast_duration"] == "6hour"


@pytest.mark.asyncio
async def test_async_setup_entry_falls_back_from_invalid_forecast_durations(hass):
    """Setup should ignore invalid stored duration option values."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={
            CONF_DAILY_FORECAST_DURATION: "30day",
            CONF_HOURLY_FORECAST_DURATION: "4day",
        },
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.twc_weather_client.TWCClient", return_value=object()
    ) as mock_client, patch(
        "custom_components.ha_weather_provider.coordinator.TWCWeatherCoordinator",
        return_value=coordinator,
    ), patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_client.call_args.kwargs["daily_forecast_duration"] == "7day"
    assert mock_client.call_args.kwargs["hourly_forecast_duration"] == "2day"


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
