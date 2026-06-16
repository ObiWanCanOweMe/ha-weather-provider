"""Optional sensor platform for HA Weather Provider."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEGREE, PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ENABLE_POLLEN,
    CONF_ENABLE_TROPICAL_WEATHER,
    CONF_EXTRA_ENTITIES,
    CONF_UNITS,
    DOMAIN,
    INTEGRATION_VERSION,
    UNIT_SYSTEMS,
)
from .coordinator import TWCWeatherCoordinator, TWCWeatherData
from .weather import (
    _condition,
    _first_daypart_value,
    _forecast_high,
    _series_value,
    _series_values,
)


SENSOR_NAME_PREFIX = "TWC"


class TWCSensorEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Describes an optional TWC companion sensor."""

    value_fn: Callable[[TWCWeatherData], Any]
    unit_key: str | None = None
    attr_fn: Callable[[TWCWeatherData], dict[str, Any]] | None = None


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
    return _timestamp_from_epoch(_value(data.current, "validTimeUtc"))


def _timestamp_from_epoch(value: Any) -> datetime | None:
    """Return an epoch value as a timezone-aware datetime."""
    if not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(value, UTC)
    except (OverflowError, OSError, ValueError):
        return None


def _current_precip_amount(data: TWCWeatherData) -> Any:
    """Return the best current-observation precipitation amount."""
    for key in ("precip1Hour", "precip6Hour", "precip24Hour", "precipAmount"):
        value = _value(data.current, key)
        if value is not None:
            return value
    return None


def _daily_daypart(data: TWCWeatherData) -> dict[str, Any]:
    """Return the first daily forecast daypart payload."""
    dayparts = data.daily_forecast.get("daypart")
    return dayparts[0] if isinstance(dayparts, list) and dayparts else {}


def _daily_condition(data: TWCWeatherData, index: int) -> str | None:
    """Return the mapped daily condition for an adapter sensor."""
    daypart = _daily_daypart(data)
    return _condition(
        _first_daypart_value(daypart, "iconCode", index),
        _first_daypart_value(daypart, "wxPhraseLong", index),
        daytime=True,
    )


def _daily_low(data: TWCWeatherData, index: int) -> Any:
    """Return the daily low temperature."""
    lows = _series_values(data.daily_forecast.get("temperatureMin"))
    return lows[index] if index < len(lows) else None


def _daily_precip_probability(data: TWCWeatherData, index: int) -> Any:
    """Return the daily precipitation probability."""
    return _first_daypart_value(_daily_daypart(data), "precipChance", index)


def _daily_precip_amount(data: TWCWeatherData, index: int) -> Any:
    """Return the daily precipitation amount."""
    return _first_daypart_value(_daily_daypart(data), "qpf", index)


def _daily_daypart_value(
    data: TWCWeatherData, key: str, index: int, *, daytime: bool
) -> Any:
    """Return an exact day or night value for a daily forecast index."""
    daypart = _daily_daypart(data)
    if not isinstance(daypart, dict):
        return None
    values = daypart.get(key)
    if not isinstance(values, list) or not values:
        return None
    series = values[0] if len(values) == 1 and isinstance(values[0], list) else values
    if not isinstance(series, list) or not series:
        return None
    day_offset = index * 2 + (1 if series[0] is None else 0)
    offset = day_offset if daytime else day_offset + 1
    if offset >= len(series):
        return None
    value = series[offset]
    if isinstance(value, list):
        return next((item for item in value if item is not None), None)
    return None if value == "" else value


def _daily_apparent_extreme(data: TWCWeatherData, index: int, *, high: bool) -> Any:
    """Return the per-day apparent temperature high or low."""
    values = [
        _daily_daypart_value(data, key, index, daytime=daytime)
        for key in ("temperatureHeatIndex", "temperatureWindChill")
        for daytime in (True, False)
    ]
    numeric_values = [
        value
        for value in values
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]
    if not numeric_values:
        return None
    return max(numeric_values) if high else min(numeric_values)


def _daily_summary(data: TWCWeatherData, index: int) -> Any:
    """Return the daily narrative summary."""
    return _series_value(data.daily_forecast, "narrative", index)


def _pollen_forecast(data: TWCWeatherData) -> dict[str, Any]:
    """Return the TWC pollen forecast segment payload."""
    pollen = data.pollen_forecast.get("pollenForecast12hour")
    return pollen if isinstance(pollen, dict) else {}


def _pollen_metadata(data: TWCWeatherData) -> dict[str, Any]:
    """Return the TWC pollen metadata payload."""
    metadata = data.pollen_forecast.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _pollen_series_value(data: TWCWeatherData, key: str, index: int = 0) -> Any:
    """Return one pollen forecast series value."""
    values = _pollen_forecast(data).get(key)
    if not isinstance(values, list) or index >= len(values):
        return None
    value = values[index]
    return None if value == "" else value


def _pollen_forecast_time(data: TWCWeatherData) -> datetime | None:
    """Return the first pollen forecast valid time."""
    return _timestamp_from_epoch(_pollen_series_value(data, "fcstValid"))


def _pollen_expiration_time(data: TWCWeatherData) -> datetime | None:
    """Return the pollen forecast expiration time."""
    return _timestamp_from_epoch(_pollen_metadata(data).get("expireTimeGmt"))


def _present(value: Any) -> bool:
    """Return whether a payload value should be exposed."""
    return value is not None and value != ""


def _first_present(*values: Any) -> Any:
    """Return the first non-empty payload value."""
    return next((value for value in values if _present(value)), None)


def _columnar_record(payload: dict[str, Any], index: int) -> dict[str, Any]:
    """Return one record from a columnar payload."""
    record: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, list):
            record[key] = value[index] if index < len(value) else None
        elif isinstance(value, dict):
            record[key] = _columnar_record(value, index)
        else:
            record[key] = value
    return record


def _records_from_tropical_segment(segment: Any) -> list[dict[str, Any]]:
    """Return tropical records from record-list or columnar payload segments."""
    if isinstance(segment, list):
        return [record for record in segment if isinstance(record, dict)]
    if not isinstance(segment, dict):
        return []

    lengths = [len(value) for value in segment.values() if isinstance(value, list)]
    if not lengths:
        return [segment]
    return [_columnar_record(segment, index) for index in range(max(lengths))]


def _tropical_records(data: TWCWeatherData) -> list[dict[str, Any]]:
    """Return active tropical storm records from supported payload shapes."""
    payload = data.tropical_current_position
    if not isinstance(payload, dict):
        return []

    for key in ("currentPosition", "current_position", "storms"):
        records = _records_from_tropical_segment(payload.get(key))
        if records:
            return records

    return _records_from_tropical_segment(payload)


def _nested_value(record: dict[str, Any], parent_key: str, *keys: str) -> Any:
    """Return a nested value from a tropical storm record."""
    nested = record.get(parent_key)
    if not isinstance(nested, dict):
        return None
    return _first_present(*(nested.get(key) for key in keys))


def _headline_value(value: Any) -> Any:
    """Return a compact headline string from a tropical storm record."""
    if isinstance(value, list):
        return _first_present(*value)
    return value


def _tropical_record_timestamp(record: dict[str, Any], *keys: str) -> datetime | None:
    """Return the first timestamp from a tropical storm record."""
    direct = _first_present(*(record.get(key) for key in keys))
    nested = _first_present(
        _nested_value(record, "advisory_info", *keys),
        _nested_value(record, "advisoryInfo", *keys),
    )
    return _timestamp_from_epoch(_first_present(direct, nested))


def _tropical_first_timestamp(data: TWCWeatherData, *keys: str) -> datetime | None:
    """Return the first matching tropical storm timestamp."""
    for record in _tropical_records(data):
        timestamp = _tropical_record_timestamp(record, *keys)
        if timestamp is not None:
            return timestamp
    return None


def _tropical_storm_summary(record: dict[str, Any]) -> dict[str, Any]:
    """Return compact attributes for one tropical storm record."""
    advisory_time = _first_present(
        _tropical_record_timestamp(record, "advisory_time_epoch", "advisoryTimeEpoch"),
        _tropical_record_timestamp(record, "process_time_epoch", "processTimeEpoch"),
    )
    expires = _tropical_record_timestamp(record, "expire_time_gmt", "expireTimeGmt")
    summary = {
        "storm_id": _first_present(record.get("storm_id"), record.get("stormId")),
        "storm_key": _first_present(record.get("storm_key"), record.get("stormKey")),
        "name": _first_present(
            record.get("storm_name"), record.get("stormName"), record.get("name")
        ),
        "basin": record.get("basin"),
        "type": _first_present(
            record.get("storm_type"), record.get("stormType"), record.get("type")
        ),
        "category": _first_present(
            record.get("storm_sub_type"),
            record.get("stormSubType"),
            record.get("category"),
        ),
        "latitude": _first_present(record.get("lat"), record.get("latitude")),
        "longitude": _first_present(record.get("lon"), record.get("longitude")),
        "max_sustained_wind": _first_present(
            record.get("max_sustained_wind"), record.get("maxSustainedWind")
        ),
        "wind_gust": _first_present(record.get("wind_gust"), record.get("windGust")),
        "minimum_pressure": _first_present(
            record.get("min_pressure"),
            record.get("minPressure"),
            record.get("minimum_pressure"),
            record.get("minimumPressure"),
        ),
        "movement_direction": _first_present(
            record.get("movement_direction"),
            record.get("movementDirection"),
            record.get("storm_dir_cardinal"),
            record.get("stormDirCardinal"),
            _nested_value(record, "heading", "storm_dir_cardinal", "stormDirCardinal"),
        ),
        "movement_speed": _first_present(
            record.get("movement_speed"),
            record.get("movementSpeed"),
            record.get("storm_speed"),
            record.get("stormSpeed"),
            _nested_value(record, "heading", "storm_speed", "stormSpeed"),
        ),
        "advisory_time": advisory_time.isoformat()
        if advisory_time is not None
        else None,
        "expires": expires.isoformat() if expires is not None else None,
        "headline": _headline_value(record.get("headline")),
    }
    return {key: value for key, value in summary.items() if _present(value)}


def _tropical_storm_summaries(data: TWCWeatherData) -> list[dict[str, Any]]:
    """Return compact active tropical storm summaries."""
    return [
        summary
        for summary in (
            _tropical_storm_summary(record) for record in _tropical_records(data)
        )
        if summary
    ]


def _tropical_storm_count(data: TWCWeatherData) -> int:
    """Return the active tropical storm count."""
    return len(_tropical_storm_summaries(data))


def _tropical_storm_state(data: TWCWeatherData) -> str:
    """Return a compact active tropical storm state."""
    count = _tropical_storm_count(data)
    if count == 0:
        return "No active storms"
    if count == 1:
        return "1 active storm"
    return f"{count} active storms"


def _tropical_storm_attributes(data: TWCWeatherData) -> dict[str, Any]:
    """Return active tropical storm attributes."""
    return {"storms": _tropical_storm_summaries(data)}


def _daily_forecast_sensor_descriptions() -> tuple[TWCSensorEntityDescription, ...]:
    """Return five days of card-friendly daily forecast adapter sensors."""
    descriptions: list[TWCSensorEntityDescription] = []
    for day in range(1, 6):
        index = day - 1
        descriptions.extend(
            (
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_condition",
                    name=f"Daily Forecast Day {day} Condition",
                    icon="mdi:weather-partly-cloudy",
                    value_fn=lambda data, index=index: _daily_condition(data, index),
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_high",
                    name=f"Daily Forecast Day {day} High",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    value_fn=lambda data, index=index: _forecast_high(
                        data.daily_forecast, index
                    ),
                    unit_key="temperature",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_low",
                    name=f"Daily Forecast Day {day} Low",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    value_fn=lambda data, index=index: _daily_low(data, index),
                    unit_key="temperature",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_precip_probability",
                    name=f"Daily Forecast Day {day} Precip Probability",
                    icon="mdi:water-percent",
                    value_fn=lambda data, index=index: _daily_precip_probability(
                        data, index
                    ),
                    unit_key="percentage",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_precip_amount",
                    name=f"Daily Forecast Day {day} Precip Amount",
                    icon="mdi:weather-rainy",
                    value_fn=lambda data, index=index: _daily_precip_amount(data, index),
                    unit_key="precipitation",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_summary",
                    name=f"Daily Forecast Day {day} Summary",
                    icon="mdi:text-short",
                    value_fn=lambda data, index=index: _daily_summary(data, index),
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_day_phrase",
                    name=f"Daily Forecast Day {day} Day Phrase",
                    icon="mdi:weather-partly-cloudy",
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "wxPhraseLong", index, daytime=True
                    ),
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_night_phrase",
                    name=f"Daily Forecast Day {day} Night Phrase",
                    icon="mdi:weather-night",
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "wxPhraseLong", index, daytime=False
                    ),
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_day_cloud_cover",
                    name=f"Daily Forecast Day {day} Day Cloud Cover",
                    icon="mdi:cloud-percent",
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "cloudCover", index, daytime=True
                    ),
                    unit_key="percentage",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_night_cloud_cover",
                    name=f"Daily Forecast Day {day} Night Cloud Cover",
                    icon="mdi:cloud-percent",
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "cloudCover", index, daytime=False
                    ),
                    unit_key="percentage",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_day_precip_probability",
                    name=f"Daily Forecast Day {day} Day Precip Probability",
                    icon="mdi:water-percent",
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "precipChance", index, daytime=True
                    ),
                    unit_key="percentage",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_night_precip_probability",
                    name=f"Daily Forecast Day {day} Night Precip Probability",
                    icon="mdi:water-percent",
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "precipChance", index, daytime=False
                    ),
                    unit_key="percentage",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_day_precip_amount",
                    name=f"Daily Forecast Day {day} Day Precip Amount",
                    icon="mdi:weather-rainy",
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "qpf", index, daytime=True
                    ),
                    unit_key="precipitation",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_night_precip_amount",
                    name=f"Daily Forecast Day {day} Night Precip Amount",
                    icon="mdi:weather-rainy",
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "qpf", index, daytime=False
                    ),
                    unit_key="precipitation",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_day_thunderstorm_probability",
                    name=f"Daily Forecast Day {day} Day Thunderstorm Probability",
                    icon="mdi:weather-lightning",
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "thunderIndex", index, daytime=True
                    ),
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_night_thunderstorm_probability",
                    name=f"Daily Forecast Day {day} Night Thunderstorm Probability",
                    icon="mdi:weather-lightning",
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "thunderIndex", index, daytime=False
                    ),
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_day_uv_index",
                    name=f"Daily Forecast Day {day} Day UV Index",
                    icon="mdi:sun-wireless",
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "uvIndex", index, daytime=True
                    ),
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_night_uv_index",
                    name=f"Daily Forecast Day {day} Night UV Index",
                    icon="mdi:sun-wireless",
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "uvIndex", index, daytime=False
                    ),
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_day_wind_speed",
                    name=f"Daily Forecast Day {day} Day Wind Speed",
                    device_class=SensorDeviceClass.WIND_SPEED,
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "windSpeed", index, daytime=True
                    ),
                    unit_key="speed",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_night_wind_speed",
                    name=f"Daily Forecast Day {day} Night Wind Speed",
                    device_class=SensorDeviceClass.WIND_SPEED,
                    value_fn=lambda data, index=index: _daily_daypart_value(
                        data, "windSpeed", index, daytime=False
                    ),
                    unit_key="speed",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_apparent_max",
                    name=f"Daily Forecast Day {day} Apparent Max",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    value_fn=lambda data, index=index: _daily_apparent_extreme(
                        data, index, high=True
                    ),
                    unit_key="temperature",
                ),
                TWCSensorEntityDescription(
                    key=f"daily_forecast_day_{day}_apparent_min",
                    name=f"Daily Forecast Day {day} Apparent Min",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    value_fn=lambda data, index=index: _daily_apparent_extreme(
                        data, index, high=False
                    ),
                    unit_key="temperature",
                ),
            )
        )
    return tuple(descriptions)


POLLEN_SENSOR_DESCRIPTIONS: tuple[TWCSensorEntityDescription, ...] = (
    TWCSensorEntityDescription(
        key="pollen_forecast_time",
        name="Pollen Forecast Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_pollen_forecast_time,
    ),
    TWCSensorEntityDescription(
        key="pollen_expiration_time",
        name="Pollen Expiration Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_pollen_expiration_time,
    ),
    TWCSensorEntityDescription(
        key="pollen_grass_index",
        name="Pollen Grass Index",
        icon="mdi:grass",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _pollen_series_value(data, "grassPollenIndex"),
    ),
    TWCSensorEntityDescription(
        key="pollen_grass_category",
        name="Pollen Grass Category",
        icon="mdi:grass",
        value_fn=lambda data: _pollen_series_value(data, "grassPollenCategory"),
    ),
    TWCSensorEntityDescription(
        key="pollen_tree_index",
        name="Pollen Tree Index",
        icon="mdi:tree",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _pollen_series_value(data, "treePollenIndex"),
    ),
    TWCSensorEntityDescription(
        key="pollen_tree_category",
        name="Pollen Tree Category",
        icon="mdi:tree",
        value_fn=lambda data: _pollen_series_value(data, "treePollenCategory"),
    ),
    TWCSensorEntityDescription(
        key="pollen_ragweed_index",
        name="Pollen Ragweed Index",
        icon="mdi:sprout",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _pollen_series_value(data, "ragweedPollenIndex"),
    ),
    TWCSensorEntityDescription(
        key="pollen_ragweed_category",
        name="Pollen Ragweed Category",
        icon="mdi:sprout",
        value_fn=lambda data: _pollen_series_value(data, "ragweedPollenCategory"),
    ),
)


TROPICAL_SENSOR_DESCRIPTIONS: tuple[TWCSensorEntityDescription, ...] = (
    TWCSensorEntityDescription(
        key="tropical_active_storm_count",
        name="Tropical Active Storm Count",
        icon="mdi:weather-hurricane",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_tropical_storm_count,
    ),
    TWCSensorEntityDescription(
        key="tropical_active_storms",
        name="Tropical Active Storms",
        icon="mdi:weather-hurricane",
        value_fn=_tropical_storm_state,
        attr_fn=_tropical_storm_attributes,
    ),
    TWCSensorEntityDescription(
        key="tropical_last_update_time",
        name="Tropical Last Update Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _tropical_first_timestamp(
            data,
            "advisory_time_epoch",
            "advisoryTimeEpoch",
            "process_time_epoch",
            "processTimeEpoch",
        ),
    ),
    TWCSensorEntityDescription(
        key="tropical_expiration_time",
        name="Tropical Expiration Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _tropical_first_timestamp(
            data,
            "expire_time_gmt",
            "expireTimeGmt",
        ),
    ),
)


COMPACT_SENSOR_DESCRIPTIONS: tuple[TWCSensorEntityDescription, ...] = (
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
    TWCSensorEntityDescription(
        key="temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "temperature"),
        unit_key="temperature",
    ),
    TWCSensorEntityDescription(
        key="feels_like_temperature",
        name="Feels Like Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "temperatureFeelsLike"),
        unit_key="temperature",
    ),
    TWCSensorEntityDescription(
        key="dew_point",
        name="Dew Point",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "temperatureDewPoint"),
        unit_key="temperature",
    ),
    TWCSensorEntityDescription(
        key="humidity",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "relativeHumidity"),
        unit_key="percentage",
    ),
    TWCSensorEntityDescription(
        key="pressure",
        name="Pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "pressureMeanSeaLevel"),
        unit_key="pressure",
    ),
    TWCSensorEntityDescription(
        key="pressure_change",
        name="Pressure Change",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "pressureChange"),
        unit_key="pressure",
    ),
    TWCSensorEntityDescription(
        key="pressure_tendency_code",
        name="Pressure Tendency Code",
        icon="mdi:gauge",
        value_fn=lambda data: _value(data.current, "pressureTendencyCode"),
    ),
    TWCSensorEntityDescription(
        key="pressure_tendency",
        name="Pressure Tendency",
        icon="mdi:gauge",
        value_fn=lambda data: _value(data.current, "pressureTendencyTrend"),
    ),
    TWCSensorEntityDescription(
        key="cloud_cover",
        name="Cloud Cover",
        icon="mdi:cloud-percent",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "cloudCover"),
        unit_key="percentage",
    ),
    TWCSensorEntityDescription(
        key="cloud_cover_phrase",
        name="Cloud Cover Phrase",
        icon="mdi:cloud",
        value_fn=lambda data: _value(data.current, "cloudCoverPhrase"),
    ),
    TWCSensorEntityDescription(
        key="cloud_ceiling",
        name="Cloud Ceiling",
        icon="mdi:cloud-upload",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "cloudCeiling"),
    ),
    TWCSensorEntityDescription(
        key="uv_index",
        name="UV Index",
        icon="mdi:sun-wireless",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "uvIndex"),
    ),
    TWCSensorEntityDescription(
        key="uv_description",
        name="UV Description",
        icon="mdi:sun-wireless",
        value_fn=lambda data: _value(data.current, "uvDescription"),
    ),
    TWCSensorEntityDescription(
        key="visibility",
        name="Visibility",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "visibility"),
        unit_key="visibility",
    ),
    TWCSensorEntityDescription(
        key="wind_speed",
        name="Wind Speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "windSpeed"),
        unit_key="speed",
    ),
    TWCSensorEntityDescription(
        key="wind_bearing",
        name="Wind Bearing",
        device_class=SensorDeviceClass.WIND_DIRECTION,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
        value_fn=lambda data: _value(data.current, "windDirection"),
        unit_key="degree",
    ),
    TWCSensorEntityDescription(
        key="precip_amount",
        name="Precip Amount",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_current_precip_amount,
        unit_key="precipitation",
    ),
    TWCSensorEntityDescription(
        key="precip_1_hour",
        name="Precip 1 Hour",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "precip1Hour"),
        unit_key="precipitation",
    ),
    TWCSensorEntityDescription(
        key="precip_6_hour",
        name="Precip 6 Hour",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "precip6Hour"),
        unit_key="precipitation",
    ),
    TWCSensorEntityDescription(
        key="precip_24_hour",
        name="Precip 24 Hour",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _value(data.current, "precip24Hour"),
        unit_key="precipitation",
    ),
    TWCSensorEntityDescription(
        key="snow_1_hour",
        name="Snow 1 Hour",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-snowy",
        value_fn=lambda data: _value(data.current, "snow1Hour"),
        unit_key="precipitation",
    ),
    TWCSensorEntityDescription(
        key="snow_6_hour",
        name="Snow 6 Hour",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-snowy",
        value_fn=lambda data: _value(data.current, "snow6Hour"),
        unit_key="precipitation",
    ),
    TWCSensorEntityDescription(
        key="snow_24_hour",
        name="Snow 24 Hour",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-snowy",
        value_fn=lambda data: _value(data.current, "snow24Hour"),
        unit_key="precipitation",
    ),
    TWCSensorEntityDescription(
        key="condition_code",
        name="Condition Code",
        icon="mdi:weather-partly-cloudy",
        value_fn=lambda data: _value(data.current, "iconCode"),
    ),
    TWCSensorEntityDescription(
        key="sunrise_time",
        name="Sunrise Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _timestamp_from_epoch(
            _value(data.current, "sunriseTimeUtc")
        ),
    ),
    TWCSensorEntityDescription(
        key="sunset_time",
        name="Sunset Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _timestamp_from_epoch(
            _value(data.current, "sunsetTimeUtc")
        ),
    ),
)


SENSOR_DESCRIPTIONS: tuple[TWCSensorEntityDescription, ...] = (
    COMPACT_SENSOR_DESCRIPTIONS + _daily_forecast_sensor_descriptions()
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up optional TWC companion sensors from a config entry."""
    descriptions: list[TWCSensorEntityDescription] = []
    if entry.options.get(CONF_EXTRA_ENTITIES, False):
        descriptions.extend(SENSOR_DESCRIPTIONS)
    if entry.options.get(CONF_ENABLE_POLLEN, False):
        descriptions.extend(POLLEN_SENSOR_DESCRIPTIONS)
    if entry.options.get(CONF_ENABLE_TROPICAL_WEATHER, False):
        descriptions.extend(TROPICAL_SENSOR_DESCRIPTIONS)
    if not descriptions:
        return

    coordinator: TWCWeatherCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TWCSensorEntity(coordinator, entry, description)
            for description in descriptions
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
        self._attr_name = f"{SENSOR_NAME_PREFIX} {description.name}"
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._units = UNIT_SYSTEMS[entry.data[CONF_UNITS]]

    @staticmethod
    def entity_descriptions() -> tuple[TWCSensorEntityDescription, ...]:
        """Return optional TWC sensor descriptions."""
        return SENSOR_DESCRIPTIONS

    @staticmethod
    def pollen_entity_descriptions() -> tuple[TWCSensorEntityDescription, ...]:
        """Return optional TWC pollen sensor descriptions."""
        return POLLEN_SENSOR_DESCRIPTIONS

    @staticmethod
    def tropical_entity_descriptions() -> tuple[TWCSensorEntityDescription, ...]:
        """Return optional TWC tropical sensor descriptions."""
        return TROPICAL_SENSOR_DESCRIPTIONS

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return sensor attributes, when configured."""
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self.coordinator.data)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the sensor unit, when the value has one."""
        if self.entity_description.unit_key is None:
            return None
        if self.entity_description.unit_key == "degree":
            return DEGREE
        if self.entity_description.unit_key == "percentage":
            return PERCENTAGE
        return self._units[self.entity_description.unit_key]
