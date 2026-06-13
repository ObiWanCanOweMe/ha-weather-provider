"""Tests for the HA Weather Provider weather platform."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from homeassistant.components.weather import WeatherEntityFeature
from homeassistant.const import UnitOfPressure

from custom_components.ha_weather_provider import const
from custom_components.ha_weather_provider.const import CONF_UNITS, DOMAIN, UNIT_SYSTEMS
from custom_components.ha_weather_provider.coordinator import TWCWeatherData
from custom_components.ha_weather_provider.weather import HAWeatherProviderEntity, async_setup_entry

_MISSING = object()
MANIFEST_PATH = Path("custom_components/ha_weather_provider/manifest.json")


def _entity(
    *,
    current: dict[str, object] | None = None,
    daily_forecast: object = _MISSING,
    hourly_forecast: object = _MISSING,
    alert_headlines: object = _MISSING,
) -> HAWeatherProviderEntity:
    coordinator = SimpleNamespace(
        data=TWCWeatherData(
            current=current
            or {
                "temperature": 72,
                "temperatureFeelsLike": 73,
                "relativeHumidity": 54,
                "pressureMeanSeaLevel": 1014.7,
                "windSpeed": 7,
                "windGust": 12,
                "windDirection": 220,
                "visibility": 10,
                "uvIndex": 6,
                "temperatureDewPoint": 55,
                "cloudCover": 41,
                "wxPhraseLong": "Partly Cloudy",
                "iconCode": 30,
            },
            daily_forecast={
                "validTimeUtc": [1718121600],
                "temperatureMax": [78],
                "temperatureMin": [61],
                "narrative": ["Partly cloudy."],
                "daypart": [
                    {
                        "wxPhraseLong": [None, "Partly Cloudy", "Mostly Clear"],
                        "iconCode": [None, 30, 33],
                        "precipChance": [None, 15, 5],
                        "qpf": [None, 0.02, 0],
                        "relativeHumidity": [None, 54, 76],
                        "temperatureHeatIndex": [None, 80, 62],
                        "temperatureWindChill": [None, 72, 58],
                        "cloudCover": [None, 38, 20],
                        "uvIndex": [None, 6, 0],
                        "windSpeed": [None, 8, 4],
                        "windDirection": [None, 210, 190],
                    }
                ],
            }
            if daily_forecast is _MISSING
            else daily_forecast,
            hourly_forecast={
                "validTimeUtc": [1718121600],
                "temperature": [72],
                "temperatureFeelsLike": [73],
                "relativeHumidity": [54],
                "pressureMeanSeaLevel": [1014.7],
                "wxPhraseLong": ["Partly Cloudy"],
                "iconCode": [30],
                "precipChance": [15],
                "qpf": [0.02],
                "windSpeed": [8],
                "windGust": [12],
                "windDirection": [210],
                "temperatureDewPoint": [55],
                "uvIndex": [6],
            }
            if hourly_forecast is _MISSING
            else hourly_forecast,
            alert_headlines={
                "alerts": [
                    {
                        "detailKey": "abc123",
                        "eventDescription": "Tornado Warning",
                        "headlineText": "Tornado Warning until 7:30 PM",
                        "severity": "Severe",
                        "severityCode": 1,
                        "urgency": "Expected",
                        "certainty": "Observed",
                        "expireTimeLocal": "2026-06-13T19:30:00-04:00",
                        "source": "NWS",
                    }
                ]
            }
            if alert_headlines is _MISSING
            else alert_headlines,
        )
    )
    entry = SimpleNamespace(
        title="TWC Weather 40.5800,-111.6600",
        entry_id="abc123",
        data={CONF_UNITS: "e"},
    )
    return HAWeatherProviderEntity(coordinator, entry)


async def test_async_setup_entry_uses_coordinator_from_hass_data(hass) -> None:
    """Weather setup should read the stored coordinator and add one entity."""
    async_add_entities = Mock()
    coordinator = object()
    entry = SimpleNamespace(
        title="TWC Weather 40.5800,-111.6600",
        entry_id="abc123",
        data={CONF_UNITS: "e"},
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await async_setup_entry(hass, entry, async_add_entities)

    entity = async_add_entities.call_args.args[0][0]
    assert entity.coordinator is coordinator
    assert entity._attr_name == "The Weather Company"
    assert entity._attr_unique_id == entry.entry_id
    assert entity.entity_id == "weather.twc"


def test_current_properties_map_twc_data() -> None:
    """Entity exposes current TWC values in native units."""
    entity = _entity()

    assert entity.supported_features == (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )
    assert entity.native_temperature == 72
    assert entity.native_apparent_temperature == 73
    assert entity.humidity == 54
    assert entity.native_pressure == 1014.7
    assert entity.native_pressure_unit == UnitOfPressure.HPA
    assert entity.native_wind_speed == 7
    assert entity.native_wind_gust_speed == 12
    assert entity.wind_bearing == 220
    assert entity.native_visibility == 10
    assert entity.uv_index == 6
    assert entity.native_dew_point == 55
    assert entity.cloud_coverage == 41
    assert entity.condition == "partlycloudy"
    assert entity.native_temperature_unit == UNIT_SYSTEMS["e"]["temperature"]


def test_entity_exposes_manifest_integration_version() -> None:
    """The weather entity should expose the manifest release version."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entity = _entity()

    assert manifest["version"] == "0.2.0"
    assert const.INTEGRATION_VERSION == manifest["version"]
    assert entity.extra_state_attributes["integration_version"] == manifest["version"]


def test_entity_exposes_alert_headline_summary_attributes() -> None:
    """The weather entity should expose compact active alert headline attributes."""
    entity = _entity()

    assert entity.extra_state_attributes["alert_count"] == 1
    assert entity.extra_state_attributes["alert_headlines"] == [
        {
            "detail_key": "abc123",
            "event": "Tornado Warning",
            "headline": "Tornado Warning until 7:30 PM",
            "severity": "Severe",
            "severity_code": 1,
            "urgency": "Expected",
            "certainty": "Observed",
            "expires": "2026-06-13T19:30:00-04:00",
            "source": "NWS",
        }
    ]


def test_entity_handles_empty_alert_headline_payload() -> None:
    """No active alerts should expose an empty alert summary."""
    entity = _entity(alert_headlines={"alerts": []})

    assert entity.extra_state_attributes["alert_count"] == 0
    assert entity.extra_state_attributes["alert_headlines"] == []


async def test_hourly_forecast_maps_twc_data() -> None:
    """Entity returns Home Assistant hourly forecast dictionaries."""
    forecast = await _entity().async_forecast_hourly()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "condition": "partlycloudy",
            "native_temperature": 72,
            "native_apparent_temperature": 73,
            "humidity": 54,
            "native_pressure": 1014.7,
            "precipitation_probability": 15,
            "native_precipitation": 0.02,
            "native_wind_speed": 8,
            "native_wind_gust_speed": 12,
            "wind_bearing": 210,
            "native_dew_point": 55,
            "uv_index": 6,
        }
    ]


async def test_hourly_forecast_skips_invalid_valid_time_entries() -> None:
    """Malformed hourly validTimeUtc entries should be skipped without crashing."""
    forecast = await _entity(
        hourly_forecast={
            "validTimeUtc": [None, "bad", 1718121600],
            "temperature": [70, 71, 72],
            "temperatureFeelsLike": [71, 72, 73],
            "relativeHumidity": [52, 53, 54],
            "pressureMeanSeaLevel": [1014.5, 1014.6, 1014.7],
            "wxPhraseLong": ["Clear", "Clear", "Partly Cloudy"],
            "iconCode": [31, 31, 30],
            "precipChance": [0, 5, 15],
            "qpf": [0, 0.01, 0.02],
            "windSpeed": [6, 7, 8],
            "windGust": [10, 11, 12],
            "windDirection": [200, 205, 210],
            "temperatureDewPoint": [53, 54, 55],
            "uvIndex": [4, 5, 6],
        }
    ).async_forecast_hourly()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "condition": "partlycloudy",
            "native_temperature": 72,
            "native_apparent_temperature": 73,
            "humidity": 54,
            "native_pressure": 1014.7,
            "precipitation_probability": 15,
            "native_precipitation": 0.02,
            "native_wind_speed": 8,
            "native_wind_gust_speed": 12,
            "wind_bearing": 210,
            "native_dew_point": 55,
            "uv_index": 6,
        }
    ]


async def test_hourly_forecast_handles_non_dict_payload() -> None:
    """Malformed hourly payloads should degrade to an empty forecast."""
    forecast = await _entity(hourly_forecast=None).async_forecast_hourly()

    assert forecast == []


async def test_daily_forecast_maps_twc_data() -> None:
    """Entity returns Home Assistant daily forecast dictionaries."""
    forecast = await _entity().async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "condition": "partlycloudy",
            "native_temperature": 78,
            "native_templow": 61,
            "native_apparent_temperature": 80,
            "humidity": 54,
            "cloud_coverage": 38,
            "precipitation_probability": 15,
            "native_precipitation": 0.02,
            "native_wind_speed": 8,
            "wind_bearing": 210,
            "uv_index": 6,
        }
    ]


async def test_daily_forecast_apparent_temperature_falls_back_to_wind_chill() -> None:
    """Daily forecast apparent temperature should use wind chill when heat index is missing."""
    forecast = await _entity(
        daily_forecast={
            "validTimeUtc": [1718121600],
            "temperatureMax": [48],
            "temperatureMin": [31],
            "daypart": [
                {
                    "wxPhraseLong": [None, "Cloudy", "Clear"],
                    "iconCode": [None, 26, 31],
                    "precipChance": [None, 20, 5],
                    "qpf": [None, 0.01, 0],
                    "relativeHumidity": [None, 62, 70],
                    "temperatureHeatIndex": [None, None, None],
                    "temperatureWindChill": [None, 42, 29],
                    "cloudCover": [None, 88, 12],
                    "uvIndex": [None, 2, 0],
                    "windSpeed": [None, 11, 6],
                    "windDirection": [None, 330, 310],
                }
            ],
        }
    ).async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "condition": "cloudy",
            "native_temperature": 48,
            "native_templow": 31,
            "native_apparent_temperature": 42,
            "humidity": 62,
            "cloud_coverage": 88,
            "precipitation_probability": 20,
            "native_precipitation": 0.01,
            "native_wind_speed": 11,
            "wind_bearing": 330,
            "uv_index": 2,
        }
    ]


async def test_daily_forecast_uses_daytime_daypart_offsets() -> None:
    """Entity should read day forecasts from interlaced daytime offsets."""
    forecast = await _entity(
        daily_forecast={
            "validTimeUtc": [1718121600, 1718208000],
            "temperatureMax": [78, 81],
            "temperatureMin": [61, 63],
            "daypart": [
                {
                    "wxPhraseLong": [None, "Partly Cloudy", "Mostly Clear", "Sunny", "Mostly Cloudy"],
                    "iconCode": [None, 30, 33, 32, 26],
                    "precipChance": [None, 15, 5, 25, 10],
                    "windSpeed": [None, 8, 4, 9, 3],
                    "windDirection": [None, 210, 190, 220, 180],
                }
            ],
        }
    ).async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "condition": "partlycloudy",
            "native_temperature": 78,
            "native_templow": 61,
            "precipitation_probability": 15,
            "native_wind_speed": 8,
            "wind_bearing": 210,
        },
        {
            "datetime": "2024-06-12T16:00:00+00:00",
            "condition": "sunny",
            "native_temperature": 81,
            "native_templow": 63,
            "precipitation_probability": 25,
            "native_wind_speed": 9,
            "wind_bearing": 220,
        },
    ]


async def test_daily_forecast_clear_phrase_without_icon_uses_sunny() -> None:
    """A daytime clear phrase should fall back to sunny."""
    forecast = await _entity(
        daily_forecast={
            "validTimeUtc": [1718121600],
            "temperatureMax": [78],
            "temperatureMin": [61],
            "daypart": [
                {
                    "wxPhraseLong": [None, "Clear", None],
                    "iconCode": [None, None, None],
                    "precipChance": [None, 0, 0],
                    "windSpeed": [None, 0, 0],
                    "windDirection": [None, None, None],
                }
            ],
        }
    ).async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "condition": "sunny",
            "native_temperature": 78,
            "native_templow": 61,
            "precipitation_probability": 0,
            "native_wind_speed": 0,
        }
    ]


async def test_daily_forecast_handles_null_daypart_entry() -> None:
    """Null daypart entries should not crash and should omit daypart-derived values."""
    forecast = await _entity(
        daily_forecast={
            "validTimeUtc": [1718121600],
            "temperatureMax": [78],
            "temperatureMin": [61],
            "daypart": [None],
        }
    ).async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "native_temperature": 78,
            "native_templow": 61,
        }
    ]


@pytest.mark.parametrize("daypart_value", [None, {}])
async def test_daily_forecast_handles_top_level_non_list_daypart(daypart_value) -> None:
    """Top-level non-list daypart payloads should degrade safely."""
    forecast = await _entity(
        daily_forecast={
            "validTimeUtc": [1718121600],
            "temperatureMax": [78],
            "temperatureMin": [61],
            "daypart": daypart_value,
        }
    ).async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "native_temperature": 78,
            "native_templow": 61,
        }
    ]


async def test_daily_forecast_uses_calendar_day_temperature_max_when_needed() -> None:
    """Forecast high should fall back to calendarDayTemperatureMax when temperatureMax is null."""
    forecast = await _entity(
        daily_forecast={
            "validTimeUtc": [1718121600],
            "temperatureMax": [None],
            "calendarDayTemperatureMax": [79],
            "temperatureMin": [61],
            "daypart": [
                {
                    "wxPhraseLong": [None, "Partly Cloudy", "Mostly Clear"],
                    "iconCode": [None, 30, 33],
                    "precipChance": [None, 15, 5],
                    "windSpeed": [None, 8, 4],
                    "windDirection": [None, 210, 190],
                }
            ],
        }
    ).async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "condition": "partlycloudy",
            "native_temperature": 79,
            "native_templow": 61,
            "precipitation_probability": 15,
            "native_wind_speed": 8,
            "wind_bearing": 210,
        }
    ]


async def test_daily_forecast_uses_flat_daypart_offsets_without_sentinel() -> None:
    """Flat daypart arrays without a sentinel should use offsets 0 and 2."""
    forecast = await _entity(
        daily_forecast={
            "validTimeUtc": [1718121600, 1718208000],
            "temperatureMax": [78, 81],
            "temperatureMin": [61, 63],
            "daypart": [
                {
                    "wxPhraseLong": ["Partly Cloudy", "Mostly Clear", "Sunny", "Mostly Cloudy"],
                    "iconCode": [30, 33, 32, 26],
                    "precipChance": [15, 5, 25, 10],
                    "windSpeed": [8, 4, 9, 3],
                    "windDirection": [210, 190, 220, 180],
                }
            ],
        }
    ).async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "condition": "partlycloudy",
            "native_temperature": 78,
            "native_templow": 61,
            "precipitation_probability": 15,
            "native_wind_speed": 8,
            "wind_bearing": 210,
        },
        {
            "datetime": "2024-06-12T16:00:00+00:00",
            "condition": "sunny",
            "native_temperature": 81,
            "native_templow": 63,
            "precipitation_probability": 25,
            "native_wind_speed": 9,
            "wind_bearing": 220,
        },
    ]


async def test_daily_forecast_skips_invalid_valid_time_entries() -> None:
    """Malformed validTimeUtc entries should be skipped without crashing."""
    forecast = await _entity(
        daily_forecast={
            "validTimeUtc": [None, "bad", 1718121600],
            "temperatureMax": [78, 79, 80],
            "temperatureMin": [61, 62, 63],
            "daypart": [
                {
                    "wxPhraseLong": ["Partly Cloudy", "Mostly Clear", "Sunny", "Mostly Cloudy", "Clear"],
                    "iconCode": [30, 33, 32, 26, 32],
                    "precipChance": [15, 5, 25, 10, 0],
                    "windSpeed": [8, 4, 9, 3, 2],
                    "windDirection": [210, 190, 220, 180, 225],
                }
            ],
        }
    ).async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "condition": "sunny",
            "native_temperature": 80,
            "native_templow": 63,
            "precipitation_probability": 0,
            "native_wind_speed": 2,
            "wind_bearing": 225,
        }
    ]


async def test_daily_forecast_handles_non_list_valid_time_series() -> None:
    """Malformed validTimeUtc containers should degrade to an empty forecast."""
    forecast = await _entity(
        daily_forecast={
            "validTimeUtc": {"bad": 1718121600},
            "temperatureMax": [78],
            "temperatureMin": [61],
            "daypart": [
                {
                    "wxPhraseLong": [None, "Partly Cloudy"],
                    "iconCode": [None, 30],
                    "precipChance": [None, 15],
                    "windSpeed": [None, 8],
                    "windDirection": [None, 210],
                }
            ],
        }
    ).async_forecast_daily()

    assert forecast == []


async def test_daily_forecast_handles_non_list_temperature_series() -> None:
    """Malformed temperature series should not crash and should still use calendar fallback."""
    forecast = await _entity(
        daily_forecast={
            "validTimeUtc": [1718121600],
            "temperatureMax": {"bad": 78},
            "calendarDayTemperatureMax": [79],
            "temperatureMin": {"bad": 61},
            "daypart": [
                {
                    "wxPhraseLong": [None, "Partly Cloudy"],
                    "iconCode": [None, 30],
                    "precipChance": [None, 15],
                    "windSpeed": [None, 8],
                    "windDirection": [None, 210],
                }
            ],
        }
    ).async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "condition": "partlycloudy",
            "native_temperature": 79,
            "precipitation_probability": 15,
            "native_wind_speed": 8,
            "wind_bearing": 210,
        }
    ]


@pytest.mark.parametrize("daily_forecast", [None, [], "bad"])
async def test_daily_forecast_handles_non_dict_top_level_payload(daily_forecast) -> None:
    """Top-level non-dict daily forecast payloads should degrade safely."""
    forecast = await _entity(daily_forecast=daily_forecast).async_forecast_daily()

    assert forecast == []


async def test_daily_forecast_uses_calendar_day_high_when_temperature_max_is_short() -> None:
    """Missing high-temperature rows should fall back to calendar day max values."""
    forecast = await _entity(
        daily_forecast={
            "validTimeUtc": [1718121600, 1718208000],
            "temperatureMax": [78],
            "calendarDayTemperatureMax": [79, 80],
            "temperatureMin": [61, 63],
            "daypart": [
                {
                    "wxPhraseLong": [None, "Partly Cloudy", "Mostly Clear", "Sunny", "Mostly Cloudy"],
                    "iconCode": [None, 30, 33, 32, 26],
                    "precipChance": [None, 15, 5, 25, 10],
                    "windSpeed": [None, 8, 4, 9, 3],
                    "windDirection": [None, 210, 190, 220, 180],
                }
            ],
        }
    ).async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "condition": "partlycloudy",
            "native_temperature": 78,
            "native_templow": 61,
            "precipitation_probability": 15,
            "native_wind_speed": 8,
            "wind_bearing": 210,
        },
        {
            "datetime": "2024-06-12T16:00:00+00:00",
            "condition": "sunny",
            "native_temperature": 80,
            "native_templow": 63,
            "precipitation_probability": 25,
            "native_wind_speed": 9,
            "wind_bearing": 220,
        },
    ]


async def test_daily_forecast_uses_calendar_day_high_when_temperature_max_is_malformed() -> None:
    """Malformed high values should still fall back to calendar day max values."""
    forecast = await _entity(
        daily_forecast={
            "validTimeUtc": [1718121600],
            "temperatureMax": [{"bad": 78}],
            "calendarDayTemperatureMax": [79],
            "temperatureMin": [61],
            "daypart": [
                {
                    "wxPhraseLong": [None, "Partly Cloudy"],
                    "iconCode": [None, 30],
                    "precipChance": [None, 15],
                    "windSpeed": [None, 8],
                    "windDirection": [None, 210],
                }
            ],
        }
    ).async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T16:00:00+00:00",
            "condition": "partlycloudy",
            "native_temperature": 79,
            "native_templow": 61,
            "precipitation_probability": 15,
            "native_wind_speed": 8,
            "wind_bearing": 210,
        }
    ]
