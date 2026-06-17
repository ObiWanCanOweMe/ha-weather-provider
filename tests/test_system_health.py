"""Tests for HA Weather Provider system health."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_weather_provider.const import (
    CONF_API_KEY,
    CONF_CURRENT_DETAIL_SENSORS,
    CONF_ENABLE_AIR_QUALITY,
    CONF_ENABLE_POLLEN,
    CONF_ENABLE_TROPICAL_WEATHER,
    CONF_FORECAST_ADAPTER_SENSORS,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_UNITS,
    DOMAIN,
    INTEGRATION_VERSION,
)
from custom_components.ha_weather_provider.coordinator import TWCWeatherData
from custom_components.ha_weather_provider.system_health import (
    async_register,
    system_health_info,
)

RAW_API_KEY = "raw-api-key-value"


class _Registration:
    """Minimal system health registration test double."""

    def __init__(self) -> None:
        self.info_callback = None

    def async_register_info(self, info_callback) -> None:
        """Capture the registered info callback."""
        self.info_callback = info_callback


def _entry() -> MockConfigEntry:
    """Return a config entry with sensitive data and optional groups enabled."""
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id="entry-id",
        data={
            CONF_API_KEY: RAW_API_KEY,
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={
            CONF_CURRENT_DETAIL_SENSORS: True,
            CONF_FORECAST_ADAPTER_SENSORS: False,
            CONF_ENABLE_POLLEN: True,
            CONF_ENABLE_TROPICAL_WEATHER: False,
            CONF_ENABLE_AIR_QUALITY: True,
        },
    )


def _coordinator() -> SimpleNamespace:
    """Return coordinator-shaped test data for system health."""
    return SimpleNamespace(
        data=TWCWeatherData(
            current={"temperature": 72},
            daily_forecast={"validTimeUtc": [1718121600]},
            hourly_forecast={},
            alert_headlines={"alerts": []},
            pollen_forecast={"pollenForecast12hour": {"grassPollenIndex": [1]}},
            pollen_observation={},
            tropical_current_position={},
            air_quality={"globalairquality": {"airQualityIndex": 61}},
        ),
        last_update_success=True,
        update_interval=timedelta(minutes=15),
        pollen_enabled=True,
        tropical_enabled=False,
        air_quality_enabled=True,
    )


async def test_system_health_registers_info_callback(hass) -> None:
    """System health platform should register its info callback."""
    registration = _Registration()

    async_register(hass, registration)

    assert registration.info_callback is system_health_info


async def test_system_health_info_reports_redacted_status(hass) -> None:
    """System health should report integration status without secrets."""
    entry = _entry()
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _coordinator()

    with patch(
        "custom_components.ha_weather_provider.system_health.system_health.async_check_can_reach_url",
        AsyncMock(return_value="ok"),
    ):
        info = await system_health_info(hass)
        can_reach_server = await info["can_reach_server"]

    assert can_reach_server == "ok"
    assert info["integration_version"] == INTEGRATION_VERSION
    assert info["configured_entries"] == 1
    assert info["configured_options"] == {
        "current_detail_sensors": True,
        "forecast_adapter_sensors": False,
        "pollen": True,
        "tropical_weather": False,
        "air_quality": True,
    }
    assert info["coordinator"]["last_update_success"] is True
    assert info["coordinator"]["enabled_optional_endpoints"] == {
        "pollen": True,
        "tropical_weather": False,
        "air_quality": True,
    }
    assert info["coordinator"]["payloads"] == {
        "current": True,
        "daily_forecast": True,
        "hourly_forecast": False,
        "alert_headlines": True,
        "pollen_forecast": True,
        "pollen_observation": False,
        "tropical_current_position": False,
        "air_quality": True,
    }
    assert RAW_API_KEY not in str(info)
    assert "40.58" not in str(info)
    assert "-111.66" not in str(info)


async def test_system_health_info_handles_no_entries(hass) -> None:
    """System health should still return basic info before configuration."""
    with patch(
        "custom_components.ha_weather_provider.system_health.system_health.async_check_can_reach_url",
        AsyncMock(return_value="ok"),
    ):
        info = await system_health_info(hass)
        can_reach_server = await info["can_reach_server"]

    assert can_reach_server == "ok"
    assert info == {
        "integration_version": INTEGRATION_VERSION,
        "configured_entries": 0,
        "can_reach_server": info["can_reach_server"],
    }
