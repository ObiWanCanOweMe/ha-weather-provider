"""Tests for HA Weather Provider diagnostics."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from homeassistant.components.diagnostics import REDACTED

from custom_components.ha_weather_provider.const import (
    CONF_API_KEY,
    CONF_ENABLE_AIR_QUALITY,
    CONF_ENABLE_POLLEN,
    CONF_ENABLE_TROPICAL_WEATHER,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_UNITS,
    DOMAIN,
    INTEGRATION_VERSION,
)
from custom_components.ha_weather_provider.coordinator import TWCWeatherData
from custom_components.ha_weather_provider.diagnostics import (
    async_get_config_entry_diagnostics,
)


RAW_API_KEY = "raw-api-key-value"


def _entry() -> SimpleNamespace:
    return SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: RAW_API_KEY,
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={
            CONF_ENABLE_POLLEN: True,
            CONF_ENABLE_TROPICAL_WEATHER: True,
            CONF_ENABLE_AIR_QUALITY: True,
        },
    )


def _coordinator() -> SimpleNamespace:
    return SimpleNamespace(
        data=TWCWeatherData(
            current={"temperature": 72},
            daily_forecast={"validTimeUtc": [1718121600]},
            hourly_forecast={"validTimeUtc": [1718121600]},
            alert_headlines={"alerts": [{"headlineText": "Storm Warning"}]},
            pollen_forecast={"pollenForecast12hour": {"grassPollenIndex": [1]}},
            pollen_observation={"pollenobservations": [{"total_pollen_cnt": 1156}]},
            tropical_current_position={"currentPosition": [{"storm_id": "AL012026"}]},
            air_quality={"globalairquality": {"airQualityIndex": 61}},
        ),
        last_update_success=True,
        update_interval=timedelta(minutes=15),
        pollen_enabled=True,
        tropical_enabled=True,
        air_quality_enabled=True,
    )


async def test_config_entry_diagnostics_redacts_config_entry_data(hass) -> None:
    """Diagnostics should redact credentials from config entry data."""
    entry = _entry()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _coordinator()

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["integration_version"] == INTEGRATION_VERSION
    assert diagnostics["config_entry"]["entry_id"] == "entry-id"
    assert diagnostics["config_entry"]["data"][CONF_API_KEY] == REDACTED
    assert diagnostics["config_entry"]["data"][CONF_LATITUDE] == REDACTED
    assert diagnostics["config_entry"]["data"][CONF_LONGITUDE] == REDACTED
    assert RAW_API_KEY not in str(diagnostics)
    assert "40.58" not in str(diagnostics)
    assert "-111.66" not in str(diagnostics)


async def test_config_entry_diagnostics_reports_options_and_coordinator(hass) -> None:
    """Diagnostics should report options and coordinator metadata."""
    entry = _entry()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _coordinator()

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["config_entry"]["options"][CONF_ENABLE_AIR_QUALITY] is True
    assert diagnostics["coordinator"]["last_update_success"] is True
    assert diagnostics["coordinator"]["update_interval_seconds"] == 900
    assert diagnostics["coordinator"]["enabled_optional_endpoints"] == {
        "pollen": True,
        "tropical_weather": True,
        "air_quality": True,
    }


async def test_config_entry_diagnostics_reports_payload_presence(hass) -> None:
    """Diagnostics should report payload presence without raw payload data."""
    entry = _entry()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _coordinator()

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["coordinator"]["payloads"] == {
        "current": True,
        "daily_forecast": True,
        "hourly_forecast": True,
        "alerts": True,
        "pollen_forecast": True,
        "pollen_observation": True,
        "tropical_current_position": True,
        "air_quality": True,
    }
    assert "temperature" not in str(diagnostics)
    assert "Storm Warning" not in str(diagnostics)
