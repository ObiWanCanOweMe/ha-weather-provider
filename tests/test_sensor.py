"""Tests for optional HA Weather Provider sensor entities."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    EntityCategory,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)

from custom_components.ha_weather_provider.const import (
    CONF_ENABLE_POLLEN,
    CONF_ENABLE_TROPICAL_WEATHER,
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

DAILY_FORECAST_SENSOR_KEYS = (
    "condition",
    "high",
    "low",
    "precip_probability",
    "precip_amount",
    "summary",
    "day_phrase",
    "night_phrase",
    "day_cloud_cover",
    "night_cloud_cover",
    "day_precip_probability",
    "night_precip_probability",
    "day_precip_amount",
    "night_precip_amount",
    "day_thunderstorm_probability",
    "night_thunderstorm_probability",
    "day_uv_index",
    "night_uv_index",
    "day_wind_speed",
    "night_wind_speed",
    "apparent_max",
    "apparent_min",
)


def _coordinator(
    *,
    daily_forecast: dict[str, object] | None = None,
    pollen_forecast: dict[str, object] | None = None,
    pollen_observation: dict[str, object] | None = None,
    tropical_current_position: dict[str, object] | None = None,
) -> SimpleNamespace:
    """Return coordinator-shaped test data for sensor entities."""
    return SimpleNamespace(
        data=TWCWeatherData(
            current={
                "cloudCover": 41,
                "cloudCoverPhrase": "Partly Cloudy",
                "cloudCeiling": 11100,
                "iconCode": 30,
                "precip1Hour": 0.04,
                "precip6Hour": 0.12,
                "precip24Hour": 0.25,
                "pressureChange": 0.04,
                "pressureMeanSeaLevel": 1014.7,
                "pressureTendencyCode": 1,
                "pressureTendencyTrend": "Rising",
                "relativeHumidity": 54,
                "snow1Hour": 0,
                "snow6Hour": 0.1,
                "snow24Hour": 0.3,
                "sunriseTimeUtc": 1718103600,
                "sunsetTimeUtc": 1718157600,
                "temperature": 72,
                "temperatureDewPoint": 55,
                "temperatureFeelsLike": 73,
                "uvDescription": "High",
                "uvIndex": 6,
                "visibility": 10,
                "windDirection": 220,
                "wxPhraseLong": "Partly Cloudy",
                "validTimeUtc": 1718121600,
                "windSpeed": 7,
                "windGust": 12,
            },
            daily_forecast=daily_forecast or {"validTimeUtc": []},
            hourly_forecast={"validTimeUtc": []},
            alert_headlines={
                "alerts": [
                    {"headlineText": "Severe Thunderstorm Warning"},
                    {"headlineText": "Flood Watch"},
                ]
            },
            pollen_forecast=pollen_forecast or {},
            pollen_observation=pollen_observation or {},
            tropical_current_position=tropical_current_position or {},
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


async def test_sensor_setup_adds_pollen_entities_when_pollen_enabled(hass) -> None:
    """Pollen sensors should be created when the pollen option is enabled."""
    async_add_entities = Mock()
    entry = _entry(options={CONF_ENABLE_POLLEN: True, CONF_EXTRA_ENTITIES: False})
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _coordinator()

    await async_setup_entry(hass, entry, async_add_entities)

    entities = async_add_entities.call_args.args[0]
    assert [entity.unique_id for entity in entities] == [
        "entry-id_pollen_forecast_time",
        "entry-id_pollen_expiration_time",
        "entry-id_pollen_grass_index",
        "entry-id_pollen_grass_category",
        "entry-id_pollen_tree_index",
        "entry-id_pollen_tree_category",
        "entry-id_pollen_ragweed_index",
        "entry-id_pollen_ragweed_category",
        "entry-id_pollen_observation_report_time",
        "entry-id_pollen_observation_expiration_time",
        "entry-id_pollen_observation_total_count",
        "entry-id_pollen_observation_total_index",
        "entry-id_pollen_observation_total_description",
        "entry-id_pollen_observation_tree_count",
        "entry-id_pollen_observation_tree_index",
        "entry-id_pollen_observation_tree_description",
        "entry-id_pollen_observation_grass_count",
        "entry-id_pollen_observation_grass_index",
        "entry-id_pollen_observation_grass_description",
        "entry-id_pollen_observation_weed_count",
        "entry-id_pollen_observation_weed_index",
        "entry-id_pollen_observation_weed_description",
        "entry-id_pollen_observation_mold_count",
        "entry-id_pollen_observation_mold_index",
        "entry-id_pollen_observation_mold_description",
    ]


async def test_sensor_setup_adds_tropical_entities_when_tropical_enabled(hass) -> None:
    """Tropical sensors should be created when the tropical option is enabled."""
    async_add_entities = Mock()
    entry = _entry(
        options={CONF_ENABLE_TROPICAL_WEATHER: True, CONF_EXTRA_ENTITIES: False}
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _coordinator()

    await async_setup_entry(hass, entry, async_add_entities)

    entities = async_add_entities.call_args.args[0]
    assert [entity.unique_id for entity in entities] == [
        "entry-id_tropical_active_storm_count",
        "entry-id_tropical_active_storms",
        "entry-id_tropical_last_update_time",
        "entry-id_tropical_expiration_time",
    ]


async def test_sensor_setup_adds_optional_entities_when_enabled(hass) -> None:
    """The first optional milestone should expose a compact diagnostic sensor set."""
    async_add_entities = Mock()
    entry = _entry(options={CONF_EXTRA_ENTITIES: True})
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _coordinator()

    await async_setup_entry(hass, entry, async_add_entities)

    entities = async_add_entities.call_args.args[0]
    assert [entity.name for entity in entities[:5]] == [
        "TWC Alert Count",
        "TWC Condition Phrase",
        "TWC Observation Time",
        "TWC Integration Version",
        "TWC Wind Gust",
    ]
    assert [entity.unique_id for entity in entities] == [
        "entry-id_alert_count",
        "entry-id_condition_phrase",
        "entry-id_observation_time",
        "entry-id_integration_version",
        "entry-id_wind_gust",
        "entry-id_temperature",
        "entry-id_feels_like_temperature",
        "entry-id_dew_point",
        "entry-id_humidity",
        "entry-id_pressure",
        "entry-id_pressure_change",
        "entry-id_pressure_tendency_code",
        "entry-id_pressure_tendency",
        "entry-id_cloud_cover",
        "entry-id_cloud_cover_phrase",
        "entry-id_cloud_ceiling",
        "entry-id_uv_index",
        "entry-id_uv_description",
        "entry-id_visibility",
        "entry-id_wind_speed",
        "entry-id_wind_bearing",
        "entry-id_precip_amount",
        "entry-id_precip_1_hour",
        "entry-id_precip_6_hour",
        "entry-id_precip_24_hour",
        "entry-id_snow_1_hour",
        "entry-id_snow_6_hour",
        "entry-id_snow_24_hour",
        "entry-id_condition_code",
        "entry-id_sunrise_time",
        "entry-id_sunset_time",
        *[
            f"entry-id_daily_forecast_day_{day}_{key}"
            for day in range(1, 6)
            for key in DAILY_FORECAST_SENSOR_KEYS
        ],
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
    assert entities["temperature"].native_value == 72
    assert entities["temperature"].native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT
    assert entities["feels_like_temperature"].native_value == 73
    assert entities["dew_point"].native_value == 55
    assert entities["humidity"].native_value == 54
    assert entities["humidity"].native_unit_of_measurement == PERCENTAGE
    assert entities["pressure"].native_value == 1014.7
    assert entities["pressure"].native_unit_of_measurement == UnitOfPressure.HPA
    assert entities["pressure_change"].native_value == 0.04
    assert entities["pressure_change"].native_unit_of_measurement == UnitOfPressure.HPA
    assert entities["pressure_tendency_code"].native_value == 1
    assert entities["pressure_tendency"].native_value == "Rising"
    assert entities["cloud_cover"].native_value == 41
    assert entities["cloud_cover"].native_unit_of_measurement == PERCENTAGE
    assert entities["cloud_cover_phrase"].native_value == "Partly Cloudy"
    assert entities["cloud_ceiling"].native_value == 11100
    assert entities["cloud_ceiling"].native_unit_of_measurement is None
    assert entities["uv_index"].native_value == 6
    assert entities["uv_description"].native_value == "High"
    assert entities["visibility"].native_value == 10
    assert entities["visibility"].native_unit_of_measurement == UnitOfLength.MILES
    assert entities["wind_speed"].native_value == 7
    assert entities["wind_speed"].native_unit_of_measurement == UnitOfSpeed.MILES_PER_HOUR
    assert entities["wind_bearing"].native_value == 220
    assert entities["wind_bearing"].native_unit_of_measurement == DEGREE
    assert entities["precip_amount"].native_value == 0.04
    assert entities["precip_amount"].native_unit_of_measurement == UnitOfLength.INCHES
    assert entities["precip_1_hour"].native_value == 0.04
    assert entities["precip_1_hour"].native_unit_of_measurement == UnitOfLength.INCHES
    assert entities["precip_6_hour"].native_value == 0.12
    assert entities["precip_6_hour"].native_unit_of_measurement == UnitOfLength.INCHES
    assert entities["precip_24_hour"].native_value == 0.25
    assert entities["precip_24_hour"].native_unit_of_measurement == UnitOfLength.INCHES
    assert entities["snow_1_hour"].native_value == 0
    assert entities["snow_1_hour"].native_unit_of_measurement == UnitOfLength.INCHES
    assert entities["snow_6_hour"].native_value == 0.1
    assert entities["snow_6_hour"].native_unit_of_measurement == UnitOfLength.INCHES
    assert entities["snow_24_hour"].native_value == 0.3
    assert entities["snow_24_hour"].native_unit_of_measurement == UnitOfLength.INCHES
    assert entities["condition_code"].native_value == 30
    assert entities["sunrise_time"].native_value == datetime(
        2024, 6, 11, 11, 0, tzinfo=UTC
    )
    assert entities["sunrise_time"].device_class == SensorDeviceClass.TIMESTAMP
    assert entities["sunset_time"].native_value == datetime(
        2024, 6, 12, 2, 0, tzinfo=UTC
    )
    assert entities["sunset_time"].device_class == SensorDeviceClass.TIMESTAMP
    assert "precip_rate" not in entities
    assert entities["observation_time"].device_class == SensorDeviceClass.TIMESTAMP
    assert entities["integration_version"].entity_category == EntityCategory.DIAGNOSTIC


def test_current_detail_sensors_are_unavailable_when_values_are_missing_or_null() -> None:
    """Current detail sensors should stay unavailable for missing, null, or blank payload values."""
    coordinator = _coordinator()
    for key in (
        "cloudCeiling",
        "pressureChange",
        "pressureTendencyTrend",
        "sunriseTimeUtc",
        "uvDescription",
    ):
        coordinator.data.current[key] = None
    for key in ("cloudCoverPhrase", "pressureTendencyCode", "sunsetTimeUtc"):
        coordinator.data.current.pop(key)
    entry = _entry(options={CONF_EXTRA_ENTITIES: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.entity_descriptions()
        ]
    }

    assert entities["pressure_change"].native_value is None
    assert entities["pressure_tendency_code"].native_value is None
    assert entities["pressure_tendency"].native_value is None
    assert entities["cloud_cover_phrase"].native_value is None
    assert entities["cloud_ceiling"].native_value is None
    assert entities["uv_description"].native_value is None
    assert entities["sunrise_time"].native_value is None
    assert entities["sunset_time"].native_value is None


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


def test_daily_forecast_adapter_sensor_values() -> None:
    """Daily forecast adapter sensors should expose card-friendly day slots."""
    coordinator = _coordinator(
        daily_forecast={
            "validTimeUtc": [1718121600, 1718208000],
            "temperatureMax": [78, 82],
            "temperatureMin": [61, 65],
            "narrative": ["Partly cloudy.", "Scattered showers."],
            "daypart": [
                {
                    "wxPhraseLong": [
                        None,
                        "Partly Cloudy",
                        "Mostly Clear",
                        "Rain Showers",
                        "Cloudy",
                    ],
                    "iconCode": [None, 30, 33, 12, 26],
                    "cloudCover": [None, 38, 20, 80, 95],
                    "precipChance": [None, 15, 5, 60, 40],
                    "qpf": [None, 0.02, 0, 0.18, 0.05],
                    "thunderIndex": [None, 1, 0, 2, 1],
                    "uvIndex": [None, 6, 0, 3, 0],
                    "windSpeed": [None, 8, 4, 12, 6],
                    "temperatureHeatIndex": [None, 80, 64, 83, 66],
                    "temperatureWindChill": [None, 72, 58, 74, 60],
                }
            ],
        }
    )
    entry = _entry(options={CONF_EXTRA_ENTITIES: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.entity_descriptions()
        ]
    }

    assert entities["daily_forecast_day_1_condition"].native_value == "partlycloudy"
    assert entities["daily_forecast_day_1_high"].native_value == 78
    assert entities["daily_forecast_day_1_high"].native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT
    assert entities["daily_forecast_day_1_low"].native_value == 61
    assert entities["daily_forecast_day_1_precip_probability"].native_value == 15
    assert entities["daily_forecast_day_1_precip_probability"].native_unit_of_measurement == PERCENTAGE
    assert entities["daily_forecast_day_1_precip_amount"].native_value == 0.02
    assert entities["daily_forecast_day_1_precip_amount"].native_unit_of_measurement == UnitOfLength.INCHES
    assert entities["daily_forecast_day_1_summary"].native_value == "Partly cloudy."
    assert entities["daily_forecast_day_1_day_phrase"].native_value == "Partly Cloudy"
    assert entities["daily_forecast_day_1_night_phrase"].native_value == "Mostly Clear"
    assert entities["daily_forecast_day_1_day_cloud_cover"].native_value == 38
    assert entities["daily_forecast_day_1_day_cloud_cover"].native_unit_of_measurement == PERCENTAGE
    assert entities["daily_forecast_day_1_night_cloud_cover"].native_value == 20
    assert entities["daily_forecast_day_1_day_precip_probability"].native_value == 15
    assert entities["daily_forecast_day_1_day_precip_probability"].native_unit_of_measurement == PERCENTAGE
    assert entities["daily_forecast_day_1_night_precip_probability"].native_value == 5
    assert entities["daily_forecast_day_1_day_precip_amount"].native_value == 0.02
    assert entities["daily_forecast_day_1_day_precip_amount"].native_unit_of_measurement == UnitOfLength.INCHES
    assert entities["daily_forecast_day_1_night_precip_amount"].native_value == 0
    assert entities["daily_forecast_day_1_day_thunderstorm_probability"].native_value == 1
    assert entities["daily_forecast_day_1_night_thunderstorm_probability"].native_value == 0
    assert entities["daily_forecast_day_1_day_uv_index"].native_value == 6
    assert entities["daily_forecast_day_1_night_uv_index"].native_value == 0
    assert entities["daily_forecast_day_1_day_wind_speed"].native_value == 8
    assert entities["daily_forecast_day_1_day_wind_speed"].native_unit_of_measurement == UnitOfSpeed.MILES_PER_HOUR
    assert entities["daily_forecast_day_1_night_wind_speed"].native_value == 4
    assert "daily_forecast_day_1_day_wind_gust" not in entities
    assert "daily_forecast_day_1_night_wind_gust" not in entities
    assert entities["daily_forecast_day_1_apparent_max"].native_value == 80
    assert entities["daily_forecast_day_1_apparent_max"].native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT
    assert entities["daily_forecast_day_1_apparent_min"].native_value == 58
    assert entities["daily_forecast_day_1_apparent_min"].native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT

    assert entities["daily_forecast_day_2_condition"].native_value == "rainy"
    assert entities["daily_forecast_day_2_high"].native_value == 82
    assert entities["daily_forecast_day_2_low"].native_value == 65
    assert entities["daily_forecast_day_2_precip_probability"].native_value == 60
    assert entities["daily_forecast_day_2_precip_amount"].native_value == 0.18
    assert entities["daily_forecast_day_2_summary"].native_value == "Scattered showers."
    assert entities["daily_forecast_day_2_day_phrase"].native_value == "Rain Showers"
    assert entities["daily_forecast_day_2_night_phrase"].native_value == "Cloudy"
    assert entities["daily_forecast_day_2_day_thunderstorm_probability"].native_value == 2
    assert entities["daily_forecast_day_2_night_thunderstorm_probability"].native_value == 1
    assert entities["daily_forecast_day_2_apparent_max"].native_value == 83
    assert entities["daily_forecast_day_2_apparent_min"].native_value == 60

    assert entities["daily_forecast_day_5_condition"].native_value is None
    assert entities["daily_forecast_day_5_day_phrase"].native_value is None


def test_pollen_sensor_values() -> None:
    """Pollen sensors should map the first forecast segment from the TWC payload."""
    coordinator = _coordinator(
        pollen_forecast={
            "metadata": {"expireTimeGmt": 1741827145},
            "pollenForecast12hour": {
                "fcstValid": [1741820400],
                "grassPollenIndex": [1],
                "grassPollenCategory": ["Low"],
                "treePollenIndex": [3],
                "treePollenCategory": ["High"],
                "ragweedPollenIndex": [0],
                "ragweedPollenCategory": ["None"],
            },
        }
    )
    entry = _entry(options={CONF_ENABLE_POLLEN: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.pollen_entity_descriptions()
        ]
    }

    assert entities["pollen_forecast_time"].native_value == datetime(
        2025, 3, 12, 23, 0, tzinfo=UTC
    )
    assert entities["pollen_forecast_time"].device_class == SensorDeviceClass.TIMESTAMP
    assert entities["pollen_expiration_time"].native_value == datetime(
        2025, 3, 13, 0, 52, 25, tzinfo=UTC
    )
    assert entities["pollen_grass_index"].native_value == 1
    assert entities["pollen_grass_category"].native_value == "Low"
    assert entities["pollen_tree_index"].native_value == 3
    assert entities["pollen_tree_category"].native_value == "High"
    assert entities["pollen_ragweed_index"].native_value == 0
    assert entities["pollen_ragweed_category"].native_value == "None"


def test_pollen_sensor_values_are_unavailable_when_payload_is_missing() -> None:
    """Pollen sensors should stay unavailable when endpoint data is absent."""
    coordinator = _coordinator(pollen_forecast={})
    entry = _entry(options={CONF_ENABLE_POLLEN: True})
    entity = next(
        entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.pollen_entity_descriptions()
        ]
        if entity.entity_description.key == "pollen_grass_index"
    )

    assert entity.native_value is None


def test_pollen_forecast_sensors_fall_back_to_observation_values() -> None:
    """Pollen forecast sensors should use observation data when forecast is absent."""
    coordinator = _coordinator(
        pollen_forecast={},
        pollen_observation={
            "pollenobservations": [
                {
                    "pollenobservation": [
                        {
                            "pollen_type": "Tree",
                            "pollen_idx": "1",
                            "pollen_desc": "Low",
                            "pollen_cnt": 15,
                        },
                        {
                            "pollen_type": "Grass",
                            "pollen_idx": "1",
                            "pollen_desc": "Low",
                            "pollen_cnt": 8,
                        },
                    ],
                }
            ],
        },
    )
    entry = _entry(options={CONF_ENABLE_POLLEN: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.pollen_entity_descriptions()
        ]
    }

    assert entities["pollen_tree_index"].native_value == 1
    assert entities["pollen_tree_category"].native_value == "Low"
    assert entities["pollen_grass_index"].native_value == 1
    assert entities["pollen_grass_category"].native_value == "Low"
    assert entities["pollen_ragweed_index"].native_value is None
    assert entities["pollen_ragweed_category"].native_value is None


def test_pollen_observation_sensor_values() -> None:
    """Pollen sensors should map U.S. observation values from the TWC payload."""
    coordinator = _coordinator(
        pollen_observation={
            "metadata": {"expire_time_gmt": 1397271306},
            "pollenobservations": [
                {
                    "class": "pollenobs",
                    "loc_id": "ATL",
                    "loc_nm": "Atlanta",
                    "loc_st": "GA",
                    "rpt_dt": "2014-04-08T15:00:00Z",
                    "process_time_gmt": 1396983306,
                    "treenames": [
                        {"tree_nm": "Oak"},
                        {"tree_nm": "Birch"},
                        {"tree_nm": "Sweet Gum"},
                    ],
                    "total_pollen_cnt": 1156,
                    "total_pollen_idx": "4",
                    "total_pollen_desc": "High",
                    "stn_cmnt_cd": "null",
                    "stn_cmnt": "null",
                    "pollenobservation": [
                        {
                            "pollen_type": "Tree",
                            "pollen_idx": "4",
                            "pollen_desc": "Very High",
                            "pollen_cnt": 1156,
                        },
                        {
                            "pollen_type": "Grass",
                            "pollen_idx": "0",
                            "pollen_desc": "None",
                            "pollen_cnt": 0,
                        },
                        {
                            "pollen_type": "Weed",
                            "pollen_idx": "0",
                            "pollen_desc": "None",
                            "pollen_cnt": 0,
                        },
                        {
                            "pollen_type": "Mold",
                            "pollen_idx": "9",
                            "pollen_desc": "No Data",
                            "pollen_cnt": None,
                        },
                    ],
                }
            ],
        }
    )
    entry = _entry(options={CONF_ENABLE_POLLEN: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.pollen_entity_descriptions()
        ]
    }

    assert entities["pollen_observation_report_time"].native_value == datetime(
        2014, 4, 8, 15, 0, tzinfo=UTC
    )
    assert (
        entities["pollen_observation_report_time"].device_class
        == SensorDeviceClass.TIMESTAMP
    )
    assert entities["pollen_observation_expiration_time"].native_value == datetime(
        2014, 4, 12, 2, 55, 6, tzinfo=UTC
    )
    assert entities["pollen_observation_total_count"].native_value == 1156
    assert entities["pollen_observation_total_index"].native_value == 4
    assert entities["pollen_observation_total_description"].native_value == "High"
    assert entities["pollen_observation_tree_count"].native_value == 1156
    assert entities["pollen_observation_tree_index"].native_value == 4
    assert entities["pollen_observation_tree_description"].native_value == "Very High"
    assert entities["pollen_observation_grass_count"].native_value == 0
    assert entities["pollen_observation_grass_index"].native_value == 0
    assert entities["pollen_observation_grass_description"].native_value == "None"
    assert entities["pollen_observation_weed_count"].native_value == 0
    assert entities["pollen_observation_weed_index"].native_value == 0
    assert entities["pollen_observation_weed_description"].native_value == "None"
    assert entities["pollen_observation_mold_count"].native_value is None
    assert entities["pollen_observation_mold_index"].native_value == 9
    assert entities["pollen_observation_mold_description"].native_value == "No Data"


def test_pollen_observation_sensor_values_are_unavailable_when_payload_is_missing() -> None:
    """Pollen observation sensors should stay unavailable when endpoint data is absent."""
    coordinator = _coordinator(pollen_observation={})
    entry = _entry(options={CONF_ENABLE_POLLEN: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.pollen_entity_descriptions()
        ]
    }

    assert entities["pollen_observation_report_time"].native_value is None
    assert entities["pollen_observation_total_count"].native_value is None
    assert entities["pollen_observation_tree_description"].native_value is None


def test_tropical_sensor_values() -> None:
    """Tropical sensors should expose compact active storm summaries."""
    coordinator = _coordinator(
        tropical_current_position={
            "currentPosition": [
                {
                    "storm_id": "AL012026",
                    "storm_key": "storm-key-1",
                    "storm_name": "Alex",
                    "basin": "AL",
                    "storm_type": "Tropical Storm",
                    "storm_sub_type": "Category 1 Hurricane",
                    "lat": 24.5,
                    "lon": -72.3,
                    "max_sustained_wind": 65,
                    "wind_gust": 80,
                    "min_pressure": 992,
                    "expire_time_gmt": 1781712000,
                    "headline": ["Alex remains offshore."],
                    "advisory_info": {
                        "advisory_time_epoch": 1781701200,
                        "process_time_epoch": 1781706300,
                    },
                    "heading": {
                        "storm_dir_cardinal": "NW",
                        "storm_speed": 12,
                    },
                }
            ]
        }
    )
    entry = _entry(options={CONF_ENABLE_TROPICAL_WEATHER: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.tropical_entity_descriptions()
        ]
    }

    assert entities["tropical_active_storm_count"].native_value == 1
    assert entities["tropical_active_storms"].native_value == "1 active storm"
    assert entities["tropical_active_storms"].extra_state_attributes == {
        "storms": [
            {
                "storm_id": "AL012026",
                "storm_key": "storm-key-1",
                "name": "Alex",
                "basin": "AL",
                "type": "Tropical Storm",
                "category": "Category 1 Hurricane",
                "latitude": 24.5,
                "longitude": -72.3,
                "max_sustained_wind": 65,
                "wind_gust": 80,
                "minimum_pressure": 992,
                "movement_direction": "NW",
                "movement_speed": 12,
                "advisory_time": "2026-06-17T13:00:00+00:00",
                "expires": "2026-06-17T16:00:00+00:00",
                "headline": "Alex remains offshore.",
            }
        ]
    }
    assert entities["tropical_last_update_time"].native_value == datetime(
        2026, 6, 17, 13, 0, tzinfo=UTC
    )
    assert (
        entities["tropical_last_update_time"].device_class
        == SensorDeviceClass.TIMESTAMP
    )
    assert entities["tropical_expiration_time"].native_value == datetime(
        2026, 6, 17, 16, 0, tzinfo=UTC
    )


def test_tropical_sensor_values_are_empty_when_payload_is_missing() -> None:
    """Tropical sensors should expose no-active-storm state for absent endpoint data."""
    coordinator = _coordinator(tropical_current_position={})
    entry = _entry(options={CONF_ENABLE_TROPICAL_WEATHER: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.tropical_entity_descriptions()
        ]
    }

    assert entities["tropical_active_storm_count"].native_value == 0
    assert entities["tropical_active_storms"].native_value == "No active storms"
    assert entities["tropical_active_storms"].extra_state_attributes == {"storms": []}
    assert entities["tropical_last_update_time"].native_value is None
    assert entities["tropical_expiration_time"].native_value is None


def test_tropical_sensor_values_from_documented_current_position_payload() -> None:
    """Tropical sensors should parse documented current-position payloads."""
    coordinator = _coordinator(
        tropical_current_position={
            "source": "all",
            "expire_time_gmt": 1749607426,
            "status_code": 200,
            "advisoryinfo": [
                {
                    "storm_key": "70f20556430be3634b82d8a49602d312",
                    "storm_id": "AL942025",
                    "storm_name": "Lee",
                    "basin": "AL",
                    "adv_dt_tm": "2025-06-04T17:00:00-04:00",
                    "process_time_gmt": 1748988499,
                    "expire_time_gmt": 1749675600,
                    "currentposition": {
                        "lat": 22.10,
                        "lon": -61.70,
                        "storm_type": "Hurricane",
                        "storm_sub_type": "Category 4 Hurricane",
                        "headline": None,
                        "min_pressure": 28.32,
                        "max_sustained_wind": 120,
                        "wind_gust": 140,
                        "heading": {
                            "storm_dir": "300",
                            "storm_dir_cardinal": "WNW",
                            "storm_spd": 8,
                        },
                    },
                }
            ],
        }
    )
    entry = _entry(options={CONF_ENABLE_TROPICAL_WEATHER: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.tropical_entity_descriptions()
        ]
    }

    assert entities["tropical_active_storm_count"].native_value == 1
    assert entities["tropical_active_storms"].native_value == "1 active storm"
    assert entities["tropical_active_storms"].extra_state_attributes == {
        "storms": [
            {
                "storm_id": "AL942025",
                "storm_key": "70f20556430be3634b82d8a49602d312",
                "name": "Lee",
                "basin": "AL",
                "type": "Hurricane",
                "category": "Category 4 Hurricane",
                "latitude": 22.10,
                "longitude": -61.70,
                "max_sustained_wind": 120,
                "wind_gust": 140,
                "minimum_pressure": 28.32,
                "movement_direction": "WNW",
                "movement_speed": 8,
                "advisory_time": "2025-06-04T17:00:00-04:00",
                "expires": "2025-06-11T21:00:00+00:00",
            }
        ]
    }
    assert entities["tropical_last_update_time"].native_value == datetime.fromisoformat(
        "2025-06-04T17:00:00-04:00"
    )
    assert entities["tropical_expiration_time"].native_value == datetime(
        2025, 6, 11, 21, 0, tzinfo=UTC
    )


def test_tropical_sensor_values_are_empty_for_empty_advisoryinfo() -> None:
    """Tropical sensors should treat an empty documented storm list as no storms."""
    coordinator = _coordinator(tropical_current_position={"advisoryinfo": []})
    entry = _entry(options={CONF_ENABLE_TROPICAL_WEATHER: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.tropical_entity_descriptions()
        ]
    }

    assert entities["tropical_active_storm_count"].native_value == 0
    assert entities["tropical_active_storms"].native_value == "No active storms"
    assert entities["tropical_active_storms"].extra_state_attributes == {"storms": []}


def test_tropical_sensor_values_are_empty_for_metadata_only_payload() -> None:
    """Tropical sensors should not count endpoint metadata as an active storm."""
    coordinator = _coordinator(
        tropical_current_position={
            "source": "all",
            "expire_time_gmt": 1749607426,
            "status_code": 200,
        }
    )
    entry = _entry(options={CONF_ENABLE_TROPICAL_WEATHER: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.tropical_entity_descriptions()
        ]
    }

    assert entities["tropical_active_storm_count"].native_value == 0
    assert entities["tropical_active_storms"].native_value == "No active storms"
    assert entities["tropical_active_storms"].extra_state_attributes == {"storms": []}


def test_tropical_timestamp_sensor_ignores_offsetless_iso_values() -> None:
    """Tropical timestamp sensors should not expose naive datetimes."""
    coordinator = _coordinator(
        tropical_current_position={
            "advisoryinfo": [
                {
                    "storm_id": "AL942025",
                    "adv_dt_tm": "2025-06-04T17:00:00",
                    "currentposition": {"lat": 22.10, "lon": -61.70},
                }
            ]
        }
    )
    entry = _entry(options={CONF_ENABLE_TROPICAL_WEATHER: True})

    entity = next(
        entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.tropical_entity_descriptions()
        ]
        if entity.entity_description.key == "tropical_last_update_time"
    )

    assert entity.native_value is None
