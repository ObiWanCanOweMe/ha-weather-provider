"""Config flow for HA Weather Provider."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_KEY,
    CONF_DAILY_FORECAST_DURATION,
    CONF_ENABLE_AIR_QUALITY,
    CONF_ENABLE_POLLEN,
    CONF_ENABLE_TROPICAL_WEATHER,
    CONF_EXTRA_ENTITIES,
    CONF_HOURLY_FORECAST_DURATION,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_UNITS,
    DAILY_FORECAST_DURATIONS,
    DEFAULT_DAILY_FORECAST_DURATION,
    DEFAULT_HOURLY_FORECAST_DURATION,
    DEFAULT_LANGUAGE,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DEFAULT_UNITS,
    DISPLAY_NAME,
    DOMAIN,
    HOURLY_FORECAST_DURATIONS,
    TWC_UNITS,
    UPDATE_INTERVAL_MINUTES,
)
from .twc_weather_client import TWCAuthError, TWCClient, TWCError, TWCPermissionError


def _validate_coordinates(latitude: float, longitude: float) -> bool:
    """Return whether coordinates are valid WGS84 latitude/longitude."""
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


class HAWeatherProviderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Weather Provider."""

    VERSION = 2

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow for this config entry."""
        return HAWeatherProviderOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            latitude = float(user_input[CONF_LATITUDE])
            longitude = float(user_input[CONF_LONGITUDE])
            units = user_input[CONF_UNITS]
            language = user_input[CONF_LANGUAGE].strip() or DEFAULT_LANGUAGE

            if not _validate_coordinates(latitude, longitude):
                errors["base"] = "invalid_coordinates"
            elif units not in TWC_UNITS:
                errors["base"] = "invalid_units"
            else:
                session = async_get_clientsession(self.hass)
                client = TWCClient(
                    session=session,
                    api_key=user_input[CONF_API_KEY],
                    latitude=latitude,
                    longitude=longitude,
                    units=units,
                    language=language,
                )
                try:
                    await client.async_get_current_conditions()
                    await client.async_get_daily_forecast()
                    await client.async_get_hourly_forecast()
                    await client.async_get_alert_headlines()
                except TWCAuthError:
                    errors["base"] = "invalid_auth"
                except TWCPermissionError:
                    errors["base"] = "not_authorized"
                except TWCError:
                    errors["base"] = "cannot_connect"
                else:
                    data = {
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_LATITUDE: latitude,
                        CONF_LONGITUDE: longitude,
                        CONF_UNITS: units,
                        CONF_LANGUAGE: language,
                    }
                    return self.async_create_entry(
                        title=DISPLAY_NAME,
                        data=data,
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_LATITUDE): vol.Coerce(float),
                vol.Required(CONF_LONGITUDE): vol.Coerce(float),
                vol.Required(CONF_UNITS, default=DEFAULT_UNITS): vol.In(TWC_UNITS),
                vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class HAWeatherProviderOptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle HA Weather Provider options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_DAILY_FORECAST_DURATION,
                    default=self.config_entry.options.get(
                        CONF_DAILY_FORECAST_DURATION,
                        DEFAULT_DAILY_FORECAST_DURATION,
                    ),
                ): vol.In(DAILY_FORECAST_DURATIONS),
                vol.Optional(
                    CONF_EXTRA_ENTITIES,
                    default=self.config_entry.options.get(CONF_EXTRA_ENTITIES, False),
                ): bool,
                vol.Optional(
                    CONF_ENABLE_POLLEN,
                    default=self.config_entry.options.get(CONF_ENABLE_POLLEN, False),
                ): bool,
                vol.Optional(
                    CONF_ENABLE_TROPICAL_WEATHER,
                    default=self.config_entry.options.get(
                        CONF_ENABLE_TROPICAL_WEATHER, False
                    ),
                ): bool,
                vol.Optional(
                    CONF_ENABLE_AIR_QUALITY,
                    default=self.config_entry.options.get(
                        CONF_ENABLE_AIR_QUALITY, False
                    ),
                ): bool,
                vol.Optional(
                    CONF_HOURLY_FORECAST_DURATION,
                    default=self.config_entry.options.get(
                        CONF_HOURLY_FORECAST_DURATION,
                        DEFAULT_HOURLY_FORECAST_DURATION,
                    ),
                ): vol.In(HOURLY_FORECAST_DURATIONS),
                vol.Optional(
                    CONF_UPDATE_INTERVAL_MINUTES,
                    default=self.config_entry.options.get(
                        CONF_UPDATE_INTERVAL_MINUTES,
                        DEFAULT_UPDATE_INTERVAL_MINUTES,
                    ),
                ): vol.In(UPDATE_INTERVAL_MINUTES),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
