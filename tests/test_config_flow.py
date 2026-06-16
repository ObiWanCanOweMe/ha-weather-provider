"""Tests for the HA Weather Provider config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_weather_provider.const import (
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
    assert result["options"] == {
        CONF_DAILY_FORECAST_DURATION: "7day",
        CONF_ENABLE_AIR_QUALITY: False,
        CONF_ENABLE_POLLEN: False,
        CONF_ENABLE_TROPICAL_WEATHER: False,
        CONF_EXTRA_ENTITIES: False,
        CONF_HOURLY_FORECAST_DURATION: "2day",
        CONF_UPDATE_INTERVAL_MINUTES: 30,
    }
    assert mock.call_args.kwargs[CONF_DAILY_FORECAST_DURATION] == "7day"
    assert mock.call_args.kwargs[CONF_HOURLY_FORECAST_DURATION] == "2day"
    client.async_get_current_conditions.assert_awaited_once()
    client.async_get_daily_forecast.assert_awaited_once()
    client.async_get_hourly_forecast.assert_awaited_once()
    client.async_get_alert_headlines.assert_awaited_once()


async def test_form_creates_entry_with_install_options(hass):
    """Initial setup should allow optional entities to be enabled."""
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
                CONF_DAILY_FORECAST_DURATION: "15day",
                CONF_ENABLE_AIR_QUALITY: True,
                CONF_ENABLE_POLLEN: True,
                CONF_ENABLE_TROPICAL_WEATHER: True,
                CONF_EXTRA_ENTITIES: True,
                CONF_HOURLY_FORECAST_DURATION: "6hour",
                CONF_UPDATE_INTERVAL_MINUTES: 15,
            },
        )

    assert result["type"] == "create_entry"
    assert result["options"] == {
        CONF_DAILY_FORECAST_DURATION: "15day",
        CONF_ENABLE_AIR_QUALITY: True,
        CONF_ENABLE_POLLEN: True,
        CONF_ENABLE_TROPICAL_WEATHER: True,
        CONF_EXTRA_ENTITIES: True,
        CONF_HOURLY_FORECAST_DURATION: "6hour",
        CONF_UPDATE_INTERVAL_MINUTES: 15,
    }
    assert mock.call_args.kwargs[CONF_DAILY_FORECAST_DURATION] == "15day"
    assert mock.call_args.kwargs[CONF_HOURLY_FORECAST_DURATION] == "6hour"


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


async def test_options_flow_configures_optional_extra_entities(hass):
    """Options flow should allow companion diagnostic sensors to be enabled."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={CONF_EXTRA_ENTITIES: False},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == "form"
    assert result["step_id"] == "init"

    with patch.object(
        hass.config_entries,
        "async_reload",
        AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_EXTRA_ENTITIES: True},
        )

    assert result["type"] == "create_entry"
    assert result["data"] == {
        CONF_DAILY_FORECAST_DURATION: "7day",
        CONF_ENABLE_AIR_QUALITY: False,
        CONF_ENABLE_POLLEN: False,
        CONF_ENABLE_TROPICAL_WEATHER: False,
        CONF_EXTRA_ENTITIES: True,
        CONF_HOURLY_FORECAST_DURATION: "2day",
        CONF_UPDATE_INTERVAL_MINUTES: 30,
    }


async def test_options_flow_configures_update_interval_controls(hass):
    """Options flow should allow update cadence to be controlled."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={
            CONF_EXTRA_ENTITIES: True,
            CONF_UPDATE_INTERVAL_MINUTES: 30,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == "form"
    assert result["step_id"] == "init"

    with patch.object(
        hass.config_entries,
        "async_reload",
        AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_EXTRA_ENTITIES: False,
                CONF_UPDATE_INTERVAL_MINUTES: 60,
            },
        )

    assert result["type"] == "create_entry"
    assert result["data"] == {
        CONF_DAILY_FORECAST_DURATION: "7day",
        CONF_ENABLE_AIR_QUALITY: False,
        CONF_ENABLE_POLLEN: False,
        CONF_ENABLE_TROPICAL_WEATHER: False,
        CONF_EXTRA_ENTITIES: False,
        CONF_HOURLY_FORECAST_DURATION: "2day",
        CONF_UPDATE_INTERVAL_MINUTES: 60,
    }


async def test_options_flow_configures_forecast_durations(hass):
    """Options flow should allow forecast endpoint durations to be controlled."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={
            CONF_DAILY_FORECAST_DURATION: "7day",
            CONF_EXTRA_ENTITIES: True,
            CONF_HOURLY_FORECAST_DURATION: "2day",
            CONF_UPDATE_INTERVAL_MINUTES: 30,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == "form"
    assert result["step_id"] == "init"

    with patch.object(
        hass.config_entries,
        "async_reload",
        AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_DAILY_FORECAST_DURATION: "15day",
                CONF_EXTRA_ENTITIES: True,
                CONF_HOURLY_FORECAST_DURATION: "6hour",
                CONF_UPDATE_INTERVAL_MINUTES: 15,
            },
        )

    assert result["type"] == "create_entry"
    assert result["data"] == {
        CONF_DAILY_FORECAST_DURATION: "15day",
        CONF_ENABLE_AIR_QUALITY: False,
        CONF_ENABLE_POLLEN: False,
        CONF_ENABLE_TROPICAL_WEATHER: False,
        CONF_EXTRA_ENTITIES: True,
        CONF_HOURLY_FORECAST_DURATION: "6hour",
        CONF_UPDATE_INTERVAL_MINUTES: 15,
    }


async def test_options_flow_configures_pollen_forecast(hass):
    """Options flow should allow the pollen forecast endpoint to be enabled."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={CONF_ENABLE_POLLEN: False},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == "form"
    assert result["step_id"] == "init"

    with patch.object(
        hass.config_entries,
        "async_reload",
        AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_ENABLE_POLLEN: True},
        )

    assert result["type"] == "create_entry"
    assert result["data"] == {
        CONF_DAILY_FORECAST_DURATION: "7day",
        CONF_ENABLE_AIR_QUALITY: False,
        CONF_ENABLE_POLLEN: True,
        CONF_ENABLE_TROPICAL_WEATHER: False,
        CONF_EXTRA_ENTITIES: False,
        CONF_HOURLY_FORECAST_DURATION: "2day",
        CONF_UPDATE_INTERVAL_MINUTES: 30,
    }


async def test_options_flow_configures_tropical_weather(hass):
    """Options flow stores the tropical weather toggle."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_DAILY_FORECAST_DURATION: "7day",
            CONF_ENABLE_AIR_QUALITY: False,
            CONF_EXTRA_ENTITIES: True,
            CONF_ENABLE_POLLEN: False,
            CONF_ENABLE_TROPICAL_WEATHER: True,
            CONF_HOURLY_FORECAST_DURATION: "2day",
            CONF_UPDATE_INTERVAL_MINUTES: 30,
        },
    )

    assert result["type"] == "create_entry"
    assert result["data"][CONF_ENABLE_TROPICAL_WEATHER] is True


async def test_options_flow_configures_air_quality(hass):
    """Options flow stores the air quality toggle."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_DAILY_FORECAST_DURATION: "7day",
            CONF_ENABLE_AIR_QUALITY: True,
            CONF_EXTRA_ENTITIES: False,
            CONF_ENABLE_POLLEN: False,
            CONF_ENABLE_TROPICAL_WEATHER: False,
            CONF_HOURLY_FORECAST_DURATION: "2day",
            CONF_UPDATE_INTERVAL_MINUTES: 30,
        },
    )

    assert result["type"] == "create_entry"
    assert result["data"][CONF_ENABLE_AIR_QUALITY] is True
