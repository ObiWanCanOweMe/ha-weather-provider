"""Weather platform for HA Weather Provider."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.weather import Forecast, WeatherEntity, WeatherEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_UNITS, DISPLAY_NAME, DOMAIN, UNIT_SYSTEMS
from .coordinator import TWCWeatherCoordinator

CONDITION_BY_ICON = {
    0: "exceptional",
    1: "exceptional",
    2: "exceptional",
    3: "lightning-rainy",
    4: "lightning-rainy",
    5: "snowy-rainy",
    6: "snowy-rainy",
    7: "snowy-rainy",
    8: "snowy-rainy",
    9: "rainy",
    10: "snowy-rainy",
    11: "rainy",
    12: "rainy",
    13: "snowy",
    14: "snowy",
    15: "snowy",
    16: "snowy",
    17: "hail",
    18: "snowy-rainy",
    19: "fog",
    20: "fog",
    21: "fog",
    22: "fog",
    23: "windy",
    24: "windy",
    25: "exceptional",
    26: "cloudy",
    27: "partlycloudy",
    28: "partlycloudy",
    29: "partlycloudy",
    30: "partlycloudy",
    31: "clear-night",
    32: "sunny",
    33: "clear-night",
    34: "sunny",
    35: "hail",
    36: "sunny",
    37: "lightning",
    38: "lightning",
    39: "rainy",
    40: "rainy",
    41: "snowy",
    42: "snowy",
    43: "snowy",
    44: "partlycloudy",
    45: "lightning-rainy",
    46: "snowy",
    47: "lightning-rainy",
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the weather entity from a config entry."""
    coordinator: TWCWeatherCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HAWeatherProviderEntity(coordinator, entry)])


def _value(data: dict[str, Any], key: str) -> Any:
    """Return a non-null value from a TWC payload."""
    value = data.get(key)
    return None if value == "" else value


def _condition(
    icon_code: Any, phrase: str | None = None, *, daytime: bool | None = None
) -> str | None:
    """Map TWC icon code or phrase to a Home Assistant condition."""
    if isinstance(icon_code, int) and icon_code in CONDITION_BY_ICON:
        return CONDITION_BY_ICON[icon_code]

    phrase = (phrase or "").lower()
    if "thunder" in phrase:
        return "lightning-rainy" if "rain" in phrase else "lightning"
    if "snow" in phrase:
        return "snowy-rainy" if "rain" in phrase else "snowy"
    if "rain" in phrase or "shower" in phrase:
        return "rainy"
    if "fog" in phrase or "mist" in phrase:
        return "fog"
    if "cloud" in phrase:
        return "partlycloudy" if "partly" in phrase or "mostly" in phrase else "cloudy"
    if "clear" in phrase:
        if daytime is True:
            return "sunny"
        return "clear-night"
    if "sun" in phrase:
        return "sunny"
    return None


def _first_daypart_value(daypart: Any, key: str, index: int) -> Any:
    """Return the first daytime value for a daily forecast index."""
    if not isinstance(daypart, dict):
        return None
    values = daypart.get(key)
    if not isinstance(values, list) or not values:
        return None
    series = values[0] if len(values) == 1 and isinstance(values[0], list) else values
    if not isinstance(series, list) or not series:
        return None
    offset = index * 2 + (1 if series[0] is None else 0)
    if offset >= len(series):
        return None
    value = series[offset]
    if isinstance(value, list):
        return next((item for item in value if item is not None), None)
    return value


def _forecast_high(daily_forecast: dict[str, Any], index: int) -> Any:
    """Return the daily high temperature, falling back to calendar day max."""
    highs = _series_values(daily_forecast.get("temperatureMax"))
    high = _series_item(highs, index)
    if high is not None:
        return high
    calendar_highs = _series_values(daily_forecast.get("calendarDayTemperatureMax"))
    return _series_item(calendar_highs, index)


def _forecast_datetime(valid_time: Any) -> str | None:
    """Convert a TWC epoch to an ISO timestamp, or skip invalid values."""
    if not isinstance(valid_time, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(valid_time, UTC).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _series_values(value: Any) -> list[Any]:
    """Return a list-like forecast series, or an empty list for malformed input."""
    return value if isinstance(value, list) else []


def _series_item(series: list[Any], index: int) -> Any:
    """Return a numeric item from a forecast series, or None for malformed values."""
    if index >= len(series):
        return None
    value = series[index]
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _series_value(data: dict[str, Any], key: str, index: int) -> Any:
    """Return one non-empty forecast series value by index."""
    series = _series_values(data.get(key))
    if index >= len(series):
        return None
    value = series[index]
    return None if value == "" else value


def _first_non_null(*values: Any) -> Any:
    """Return the first non-null, non-empty value."""
    return next((value for value in values if value is not None and value != ""), None)


class HAWeatherProviderEntity(CoordinatorEntity[TWCWeatherCoordinator], WeatherEntity):
    """Representation of a TWC weather entity."""

    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(self, coordinator: TWCWeatherCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = DISPLAY_NAME
        self._attr_unique_id = entry.entry_id
        self._units = UNIT_SYSTEMS[entry.data[CONF_UNITS]]

    @property
    def current(self) -> dict[str, Any]:
        """Return current TWC conditions."""
        return self.coordinator.data.current

    @property
    def native_temperature(self) -> float | None:
        return _value(self.current, "temperature")

    @property
    def native_temperature_unit(self) -> str:
        return self._units["temperature"]

    @property
    def native_apparent_temperature(self) -> float | None:
        return _value(self.current, "temperatureFeelsLike")

    @property
    def humidity(self) -> float | None:
        return _value(self.current, "relativeHumidity")

    @property
    def native_pressure(self) -> float | None:
        return _value(self.current, "pressureMeanSeaLevel")

    @property
    def native_pressure_unit(self) -> str:
        return self._units["pressure"]

    @property
    def native_wind_speed(self) -> float | None:
        return _value(self.current, "windSpeed")

    @property
    def native_wind_gust_speed(self) -> float | None:
        return _value(self.current, "windGust")

    @property
    def native_wind_speed_unit(self) -> str:
        return self._units["speed"]

    @property
    def wind_bearing(self) -> int | str | None:
        return _value(self.current, "windDirection")

    @property
    def native_visibility(self) -> float | None:
        return _value(self.current, "visibility")

    @property
    def native_visibility_unit(self) -> str:
        return self._units["visibility"]

    @property
    def uv_index(self) -> float | None:
        return _value(self.current, "uvIndex")

    @property
    def native_dew_point(self) -> float | None:
        return _value(self.current, "temperatureDewPoint")

    @property
    def cloud_coverage(self) -> float | None:
        return _value(self.current, "cloudCover")

    @property
    def condition(self) -> str | None:
        return _condition(_value(self.current, "iconCode"), _value(self.current, "wxPhraseLong"))

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        data = self.coordinator.data.daily_forecast
        if not isinstance(data, dict):
            return []
        valid_times = _series_values(data.get("validTimeUtc"))
        lows = _series_values(data.get("temperatureMin"))
        dayparts = data.get("daypart")
        daypart = dayparts[0] if isinstance(dayparts, list) and dayparts else {}

        forecasts: list[Forecast] = []
        for index, valid_time in enumerate(valid_times):
            forecast_datetime = _forecast_datetime(valid_time)
            if forecast_datetime is None:
                continue
            forecast: Forecast = {
                "datetime": forecast_datetime,
                "condition": _condition(
                    _first_daypart_value(daypart, "iconCode", index),
                    _first_daypart_value(daypart, "wxPhraseLong", index),
                    daytime=True,
                ),
                "native_temperature": _forecast_high(data, index),
                "native_templow": lows[index] if index < len(lows) else None,
                "native_apparent_temperature": _first_non_null(
                    _first_daypart_value(daypart, "temperatureHeatIndex", index),
                    _first_daypart_value(daypart, "temperatureWindChill", index),
                ),
                "humidity": _first_daypart_value(daypart, "relativeHumidity", index),
                "cloud_coverage": _first_daypart_value(daypart, "cloudCover", index),
                "precipitation_probability": _first_daypart_value(daypart, "precipChance", index),
                "native_precipitation": _first_daypart_value(daypart, "qpf", index),
                "native_wind_speed": _first_daypart_value(daypart, "windSpeed", index),
                "wind_bearing": _first_daypart_value(daypart, "windDirection", index),
                "uv_index": _first_daypart_value(daypart, "uvIndex", index),
            }
            forecasts.append({key: value for key, value in forecast.items() if value is not None})

        return forecasts

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the 2-day hourly forecast in native units."""
        data = self.coordinator.data.hourly_forecast
        if not isinstance(data, dict):
            return []
        valid_times = _series_values(data.get("validTimeUtc"))

        forecasts: list[Forecast] = []
        for index, valid_time in enumerate(valid_times):
            forecast_datetime = _forecast_datetime(valid_time)
            if forecast_datetime is None:
                continue
            forecast: Forecast = {
                "datetime": forecast_datetime,
                "condition": _condition(
                    _series_value(data, "iconCode", index),
                    _series_value(data, "wxPhraseLong", index),
                ),
                "native_temperature": _series_value(data, "temperature", index),
                "native_apparent_temperature": _series_value(
                    data, "temperatureFeelsLike", index
                ),
                "humidity": _series_value(data, "relativeHumidity", index),
                "native_pressure": _series_value(data, "pressureMeanSeaLevel", index),
                "precipitation_probability": _series_value(
                    data, "precipChance", index
                ),
                "native_precipitation": _series_value(data, "qpf", index),
                "native_wind_speed": _series_value(data, "windSpeed", index),
                "native_wind_gust_speed": _series_value(data, "windGust", index),
                "wind_bearing": _series_value(data, "windDirection", index),
                "native_dew_point": _series_value(data, "temperatureDewPoint", index),
                "uv_index": _series_value(data, "uvIndex", index),
            }
            forecasts.append({key: value for key, value in forecast.items() if value is not None})

        return forecasts
