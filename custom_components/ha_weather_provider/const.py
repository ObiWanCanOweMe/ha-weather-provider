"""Constants for the HA Weather Provider integration."""

from __future__ import annotations

from datetime import timedelta

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

DEFAULT_LANGUAGE = "en-US"
DEFAULT_UNITS = "e"
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=30)
DISPLAY_NAME = "The Weather Company"

TWC_UNITS = {
    "e": "English",
    "m": "Metric",
    "h": "Hybrid UK",
    "s": "Metric SI",
}

UNIT_SYSTEMS = {
    "e": {
        "temperature": UnitOfTemperature.FAHRENHEIT,
        "pressure": UnitOfPressure.INHG,
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
        "pressure": UnitOfPressure.MBAR,
        "speed": UnitOfSpeed.MILES_PER_HOUR,
        "precipitation": UnitOfLength.MILLIMETERS,
        "visibility": UnitOfLength.MILES,
    },
    "s": {
        "temperature": UnitOfTemperature.CELSIUS,
        "pressure": UnitOfPressure.PA,
        "speed": UnitOfSpeed.METERS_PER_SECOND,
        "precipitation": UnitOfLength.MILLIMETERS,
        "visibility": UnitOfLength.METERS,
    },
}
