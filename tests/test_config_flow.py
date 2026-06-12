"""Tests for the HA Weather Provider config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries

from custom_components.ha_weather_provider.const import (
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_UNITS,
    DOMAIN,
)


async def test_form_creates_entry(hass):
    """Valid user input creates a config entry."""
    with patch("custom_components.ha_weather_provider.config_flow.TWCClient") as mock:
        client = mock.return_value
        client.async_get_current_conditions = AsyncMock(return_value={"temperature": 71})

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_API_KEY: "secret",
                CONF_LATITUDE: 40.58,
                CONF_LONGITUDE: -111.66,
                CONF_UNITS: "e",
                CONF_LANGUAGE: "en-US",
            },
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "TWC Weather 40.5800,-111.6600"
    assert result["data"][CONF_API_KEY] == "secret"
    assert result["data"][CONF_LATITUDE] == 40.58
    assert result["data"][CONF_LONGITUDE] == -111.66
    assert result["data"][CONF_UNITS] == "e"
    assert result["data"][CONF_LANGUAGE] == "en-US"


async def test_form_rejects_invalid_coordinates(hass):
    """Out-of-range coordinates show an error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 91,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
    )

    assert result["type"] == "form"
    assert result["errors"]["base"] == "invalid_coordinates"


async def test_form_rejects_bad_auth(hass):
    """Authentication errors surface as invalid auth."""
    from custom_components.ha_weather_provider.api import TWCAuthError

    with patch("custom_components.ha_weather_provider.config_flow.TWCClient") as mock:
        client = mock.return_value
        client.async_get_current_conditions = AsyncMock(side_effect=TWCAuthError("bad"))

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_API_KEY: "bad",
                CONF_LATITUDE: 40.58,
                CONF_LONGITUDE: -111.66,
                CONF_UNITS: "e",
                CONF_LANGUAGE: "en-US",
            },
        )

    assert result["type"] == "form"
    assert result["errors"]["base"] == "invalid_auth"


async def test_form_rejects_temporary_client_failure(hass):
    """The temporary client shell should fail as a connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
    )

    assert result["type"] == "form"
    assert result["errors"]["base"] == "cannot_connect"
