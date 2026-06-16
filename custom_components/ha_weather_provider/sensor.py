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

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

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
