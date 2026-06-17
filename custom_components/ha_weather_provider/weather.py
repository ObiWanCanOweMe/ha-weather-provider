"""Weather platform for HA Weather Provider."""

from __future__ import annotations

from typing import Any

from homeassistant.components.weather import (
    CoordinatorWeatherEntity,
    Forecast,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import (
    CONF_UNITS,
    DEFAULT_ENTITY_ID,
    DISPLAY_NAME,
    DOMAIN,
    INTEGRATION_VERSION,
    UNIT_SYSTEMS,
)
from .coordinator import (
    TWCDailyForecastCoordinator,
    TWCHourlyForecastCoordinator,
    TWCObservationCoordinator,
    TWCWeatherCoordinator,
)
from .twc_weather_client.normalizers import (
    alert_summaries as _alert_summaries,
    condition_from_twc as _condition,
    first_daypart_value as _first_daypart_value,
    first_non_null as _first_non_null,
    forecast_datetime as _forecast_datetime,
    series_item as _series_item,
    series_value as _series_value,
    series_values as _series_values,
    value as _value,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the weather entity from a config entry."""
    coordinator: TWCWeatherCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HAWeatherProviderEntity(coordinator, entry)])


def _forecast_high(daily_forecast: dict[str, Any], index: int) -> Any:
    """Return the daily high temperature, falling back to calendar day max."""
    highs = _series_values(daily_forecast.get("temperatureMax"))
    high = _series_item(highs, index)
    if high is not None:
        return high
    calendar_highs = _series_values(daily_forecast.get("calendarDayTemperatureMax"))
    return _series_item(calendar_highs, index)


class HAWeatherProviderEntity(
    CoordinatorWeatherEntity[
        TWCObservationCoordinator,
        TWCDailyForecastCoordinator,
        TWCHourlyForecastCoordinator,
        None,
    ]
):
    """Representation of a TWC weather entity."""

    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(self, coordinator: TWCWeatherCoordinator, entry: ConfigEntry) -> None:
        super().__init__(
            coordinator.observation_coordinator,
            daily_coordinator=coordinator.daily_forecast_coordinator,
            hourly_coordinator=coordinator.hourly_forecast_coordinator,
        )
        self._entry = entry
        self._twc_coordinator = coordinator
        self.daily_coordinator = coordinator.daily_forecast_coordinator
        self.hourly_coordinator = coordinator.hourly_forecast_coordinator
        self.alert_coordinator = coordinator.alert_coordinator
        self._attr_name = DISPLAY_NAME
        self._attr_unique_id = entry.entry_id
        self.entity_id = DEFAULT_ENTITY_ID
        self._units = UNIT_SYSTEMS[entry.data[CONF_UNITS]]
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=DISPLAY_NAME,
            name=DISPLAY_NAME,
        )

    @property
    def current(self) -> dict[str, Any]:
        """Return current TWC conditions."""
        return self.coordinator.data or {}

    @property
    def alert_headlines(self) -> dict[str, Any]:
        """Return active TWC alert headlines."""
        return self.alert_coordinator.data or {}

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        alert_headlines = _alert_summaries(self.alert_headlines)
        return {
            "integration_version": INTEGRATION_VERSION,
            "alert_count": len(alert_headlines),
            "alert_headlines": alert_headlines,
        }

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
    def cloud_coverage(self) -> int | None:
        return _value(self.current, "cloudCover")

    @property
    def condition(self) -> str | None:
        return _condition(_value(self.current, "iconCode"), _value(self.current, "wxPhraseLong"))

    def _async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        data = self.daily_coordinator.data if self.daily_coordinator else None
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
                "native_dew_point": _first_daypart_value(
                    daypart, "temperatureDewPoint", index
                ),
                "cloud_coverage": _first_daypart_value(daypart, "cloudCover", index),
                "precipitation_probability": _first_daypart_value(daypart, "precipChance", index),
                "native_precipitation": _first_daypart_value(daypart, "qpf", index),
                "native_wind_speed": _first_daypart_value(daypart, "windSpeed", index),
                "wind_bearing": _first_daypart_value(daypart, "windDirection", index),
                "uv_index": _first_daypart_value(daypart, "uvIndex", index),
            }
            forecasts.append({key: value for key, value in forecast.items() if value is not None})

        return forecasts

    def _async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the 2-day hourly forecast in native units."""
        data = self.hourly_coordinator.data if self.hourly_coordinator else None
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
                "cloud_coverage": _series_value(data, "cloudCover", index),
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
