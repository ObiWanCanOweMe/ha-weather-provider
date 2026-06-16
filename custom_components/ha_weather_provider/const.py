"""Constants for the HA Weather Provider integration."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from homeassistant.const import (
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)

DOMAIN = "ha_weather_provider"

CONF_API_KEY = "api_key"
CONF_LANGUAGE = "language"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_UNITS = "units"
CONF_EXTRA_ENTITIES = "extra_entities"
CONF_ENABLE_POLLEN = "enable_pollen"
CONF_ENABLE_TROPICAL_WEATHER = "enable_tropical_weather"
CONF_UPDATE_INTERVAL_MINUTES = "update_interval_minutes"
CONF_DAILY_FORECAST_DURATION = "daily_forecast_duration"
CONF_HOURLY_FORECAST_DURATION = "hourly_forecast_duration"

DEFAULT_LANGUAGE = "en-US"
DEFAULT_UNITS = "e"
DEFAULT_UPDATE_INTERVAL_MINUTES = 30
DEFAULT_DAILY_FORECAST_DURATION = "7day"
DEFAULT_HOURLY_FORECAST_DURATION = "2day"
DEFAULT_POLLEN_FORECAST_DURATION = "3day"
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=DEFAULT_UPDATE_INTERVAL_MINUTES)
DISPLAY_NAME = "The Weather Company"
DEFAULT_ENTITY_ID = "weather.twc"
INTEGRATION_VERSION = json.loads(Path(__file__).with_name("manifest.json").read_text())["version"]
UPDATE_INTERVAL_MINUTES = (15, 30, 60)
DAILY_FORECAST_DURATIONS = ("3day", "5day", "7day", "10day", "15day")
HOURLY_FORECAST_DURATIONS = (
    "6hour",
    "12hour",
    "1day",
    "2day",
    "3day",
    "10day",
    "15day",
)

TWC_UNITS = {
    "e": "English",
    "m": "Metric",
    "h": "Hybrid UK",
    "s": "Metric SI",
}

UNIT_SYSTEMS = {
    "e": {
        "temperature": UnitOfTemperature.FAHRENHEIT,
        "pressure": UnitOfPressure.HPA,
        "speed": UnitOfSpeed.MILES_PER_HOUR,
        "precipitation": UnitOfLength.INCHES,
        "visibility": UnitOfLength.MILES,
    },
    "m": {
        "temperature": UnitOfTemperature.CELSIUS,
        "pressure": UnitOfPressure.HPA,
        "speed": UnitOfSpeed.KILOMETERS_PER_HOUR,
        "precipitation": UnitOfLength.MILLIMETERS,
        "visibility": UnitOfLength.KILOMETERS,
    },
    "h": {
        "temperature": UnitOfTemperature.CELSIUS,
        "pressure": UnitOfPressure.HPA,
        "speed": UnitOfSpeed.MILES_PER_HOUR,
        "precipitation": UnitOfLength.MILLIMETERS,
        "visibility": UnitOfLength.MILES,
    },
    "s": {
        "temperature": UnitOfTemperature.CELSIUS,
        "pressure": UnitOfPressure.HPA,
        "speed": UnitOfSpeed.METERS_PER_SECOND,
        "precipitation": UnitOfLength.MILLIMETERS,
        "visibility": UnitOfLength.METERS,
    },
}
