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
        client.async_get_daily_forecast = AsyncMock(return_value={"validTimeUtc": []})
        client.async_get_hourly_forecast = AsyncMock(return_value={"validTimeUtc": []})
        client.async_get_alert_headlines = AsyncMock(return_value={"alerts": []})

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
    assert result["title"] == "The Weather Company"
    assert result["data"][CONF_API_KEY] == "secret"
    assert result["data"][CONF_LATITUDE] == 40.58
    assert result["data"][CONF_LONGITUDE] == -111.66
    assert result["data"][CONF_UNITS] == "e"
    assert result["data"][CONF_LANGUAGE] == "en-US"
    client.async_get_current_conditions.assert_awaited_once()
    client.async_get_daily_forecast.assert_awaited_once()
    client.async_get_hourly_forecast.assert_awaited_once()
    client.async_get_alert_headlines.assert_awaited_once()


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
        client.async_get_daily_forecast = AsyncMock()
        client.async_get_hourly_forecast = AsyncMock()
        client.async_get_alert_headlines = AsyncMock()

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
    client.async_get_daily_forecast.assert_not_called()
    client.async_get_hourly_forecast.assert_not_called()
    client.async_get_alert_headlines.assert_not_called()


async def test_form_rejects_daily_forecast_auth_failure(hass):
    """Daily forecast authorization errors are caught during setup validation."""
    from custom_components.ha_weather_provider.api import TWCPermissionError

    with patch("custom_components.ha_weather_provider.config_flow.TWCClient") as mock:
        client = mock.return_value
        client.async_get_current_conditions = AsyncMock(return_value={"temperature": 71})
        client.async_get_daily_forecast = AsyncMock(
            side_effect=TWCPermissionError("daily denied")
        )
        client.async_get_hourly_forecast = AsyncMock()
        client.async_get_alert_headlines = AsyncMock()

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
    assert result["errors"]["base"] == "not_authorized"
    client.async_get_hourly_forecast.assert_not_called()
    client.async_get_alert_headlines.assert_not_called()


async def test_form_rejects_hourly_forecast_auth_failure(hass):
    """Hourly forecast authorization errors are caught during setup validation."""
    from custom_components.ha_weather_provider.api import TWCPermissionError

    with patch("custom_components.ha_weather_provider.config_flow.TWCClient") as mock:
        client = mock.return_value
        client.async_get_current_conditions = AsyncMock(return_value={"temperature": 71})
        client.async_get_daily_forecast = AsyncMock(return_value={"validTimeUtc": []})
        client.async_get_hourly_forecast = AsyncMock(
            side_effect=TWCPermissionError("hourly denied")
        )
        client.async_get_alert_headlines = AsyncMock()

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
    assert result["errors"]["base"] == "not_authorized"
    client.async_get_alert_headlines.assert_not_called()


async def test_form_rejects_alert_headlines_auth_failure(hass):
    """Alert headline authorization errors are caught during setup validation."""
    from custom_components.ha_weather_provider.api import TWCPermissionError

    with patch("custom_components.ha_weather_provider.config_flow.TWCClient") as mock:
        client = mock.return_value
        client.async_get_current_conditions = AsyncMock(return_value={"temperature": 71})
        client.async_get_daily_forecast = AsyncMock(return_value={"validTimeUtc": []})
        client.async_get_hourly_forecast = AsyncMock(return_value={"validTimeUtc": []})
        client.async_get_alert_headlines = AsyncMock(
            side_effect=TWCPermissionError("alerts denied")
        )

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
    assert result["errors"]["base"] == "not_authorized"


async def test_form_rejects_request_error(hass):
    """Generic TWC failures surface as connection errors."""
    from custom_components.ha_weather_provider.api import TWCRequestError

    with patch("custom_components.ha_weather_provider.config_flow.TWCClient") as mock:
        client = mock.return_value
        client.async_get_current_conditions = AsyncMock(
            side_effect=TWCRequestError("down")
        )
        client.async_get_daily_forecast = AsyncMock()
        client.async_get_hourly_forecast = AsyncMock()
        client.async_get_alert_headlines = AsyncMock()

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
    client.async_get_daily_forecast.assert_not_called()
    client.async_get_hourly_forecast.assert_not_called()
    client.async_get_alert_headlines.assert_not_called()
