"""Config flow for HA Weather Provider."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import CONF_API_KEY, CONF_LOCATION, DOMAIN


class HAWeatherProviderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Weather Provider."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_LOCATION], data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_LOCATION): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
