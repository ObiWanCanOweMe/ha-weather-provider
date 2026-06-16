"""Tests for the HA Weather Provider coordinator."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.ha_weather_provider.api import (
    TWCAuthError,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)
from custom_components.ha_weather_provider.coordinator import (
    TWCWeatherCoordinator,
    TWCWeatherData,
)


@pytest.mark.asyncio
async def test_coordinator_combines_current_and_forecast(hass) -> None:
    """Coordinator should merge current and forecast payloads."""
    client = AsyncMock()
    client.async_get_current_conditions.return_value = {"temperature": 72}
    client.async_get_daily_forecast.return_value = {"temperatureMax": [75]}
    client.async_get_hourly_forecast.return_value = {"temperature": [72, 71]}
    client.async_get_alert_headlines.return_value = {
        "alerts": [{"eventDescription": "Tornado Warning"}]
    }
    coordinator = TWCWeatherCoordinator(hass, client)

    data = await coordinator._async_update_data()

    assert data == TWCWeatherData(
        current={"temperature": 72},
        daily_forecast={"temperatureMax": [75]},
        hourly_forecast={"temperature": [72, 71]},
        alert_headlines={"alerts": [{"eventDescription": "Tornado Warning"}]},
        pollen_forecast={},
        pollen_observation={},
        tropical_current_position={},
        air_quality={},
    )
    client.async_get_pollen_forecast.assert_not_called()
    client.async_get_tropical_current_position.assert_not_called()
    client.async_get_air_quality.assert_not_called()


@pytest.mark.asyncio
async def test_coordinator_fetches_pollen_when_enabled(hass) -> None:
    """Coordinator should merge pollen forecast data when pollen is enabled."""
    client = AsyncMock()
    client.async_get_current_conditions.return_value = {"temperature": 72}
    client.async_get_daily_forecast.return_value = {"temperatureMax": [75]}
    client.async_get_hourly_forecast.return_value = {"temperature": [72, 71]}
    client.async_get_alert_headlines.return_value = {"alerts": []}
    client.async_get_pollen_forecast.return_value = {
        "pollenForecast12hour": {"grassPollenIndex": [1]}
    }
    client.async_get_pollen_observation.return_value = {
        "pollenobservations": [{"total_pollen_cnt": 1156}]
    }
    coordinator = TWCWeatherCoordinator(hass, client, pollen_enabled=True)

    data = await coordinator._async_update_data()

    assert data.pollen_forecast == {
        "pollenForecast12hour": {"grassPollenIndex": [1]}
    }
    assert data.pollen_observation == {
        "pollenobservations": [{"total_pollen_cnt": 1156}]
    }
    client.async_get_pollen_forecast.assert_awaited_once()
    client.async_get_pollen_observation.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        TWCNoDataError("empty"),
        TWCAuthError("bad key for optional endpoint"),
        TWCPermissionError("no access"),
    ],
)
async def test_coordinator_keeps_weather_data_when_optional_pollen_unavailable(
    hass, error
) -> None:
    """Optional pollen endpoint availability and entitlement failures should not fail refresh."""
    client = AsyncMock()
    client.async_get_current_conditions.return_value = {"temperature": 72}
    client.async_get_daily_forecast.return_value = {"temperatureMax": [75]}
    client.async_get_hourly_forecast.return_value = {"temperature": [72, 71]}
    client.async_get_alert_headlines.return_value = {"alerts": []}
    client.async_get_pollen_forecast.side_effect = error
    client.async_get_pollen_observation.return_value = {
        "pollenobservations": [{"total_pollen_cnt": 1156}]
    }
    coordinator = TWCWeatherCoordinator(hass, client, pollen_enabled=True)

    data = await coordinator._async_update_data()

    assert data.current == {"temperature": 72}
    assert data.pollen_forecast == {}
    assert data.pollen_observation == {
        "pollenobservations": [{"total_pollen_cnt": 1156}]
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        TWCNoDataError("empty"),
        TWCAuthError("bad key for optional endpoint"),
        TWCPermissionError("no access"),
        TWCRequestError("temporary pollen observation failure"),
    ],
)
async def test_coordinator_keeps_weather_data_when_optional_pollen_observation_unavailable(
    hass, error
) -> None:
    """Optional pollen observation endpoint failures should not fail refresh."""
    client = AsyncMock()
    client.async_get_current_conditions.return_value = {"temperature": 72}
    client.async_get_daily_forecast.return_value = {"temperatureMax": [75]}
    client.async_get_hourly_forecast.return_value = {"temperature": [72, 71]}
    client.async_get_alert_headlines.return_value = {"alerts": []}
    client.async_get_pollen_forecast.return_value = {
        "pollenForecast12hour": {"grassPollenIndex": [1]}
    }
    client.async_get_pollen_observation.side_effect = error
    coordinator = TWCWeatherCoordinator(hass, client, pollen_enabled=True)

    data = await coordinator._async_update_data()

    assert data.current == {"temperature": 72}
    assert data.pollen_forecast == {
        "pollenForecast12hour": {"grassPollenIndex": [1]}
    }
    assert data.pollen_observation == {}


@pytest.mark.asyncio
async def test_coordinator_fetches_tropical_when_enabled(hass) -> None:
    """Coordinator should merge tropical current-position data when enabled."""
    client = AsyncMock()
    client.async_get_current_conditions.return_value = {"temperature": 72}
    client.async_get_daily_forecast.return_value = {"temperatureMax": [75]}
    client.async_get_hourly_forecast.return_value = {"temperature": [72, 71]}
    client.async_get_alert_headlines.return_value = {"alerts": []}
    client.async_get_tropical_current_position.return_value = {
        "currentPosition": [{"storm_id": "AL012026"}]
    }
    coordinator = TWCWeatherCoordinator(hass, client, tropical_enabled=True)

    data = await coordinator._async_update_data()

    assert data.tropical_current_position == {
        "currentPosition": [{"storm_id": "AL012026"}]
    }
    client.async_get_tropical_current_position.assert_awaited_once()


@pytest.mark.asyncio
async def test_coordinator_fetches_air_quality_when_enabled(hass) -> None:
    """Coordinator should merge air quality data when enabled."""
    client = AsyncMock()
    client.async_get_current_conditions.return_value = {"temperature": 72}
    client.async_get_daily_forecast.return_value = {"temperatureMax": [75]}
    client.async_get_hourly_forecast.return_value = {"temperature": [72, 71]}
    client.async_get_alert_headlines.return_value = {"alerts": []}
    client.async_get_air_quality.return_value = {
        "globalairquality": {"airQualityIndex": 61}
    }
    coordinator = TWCWeatherCoordinator(hass, client, air_quality_enabled=True)

    data = await coordinator._async_update_data()

    assert data.air_quality == {"globalairquality": {"airQualityIndex": 61}}
    client.async_get_air_quality.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        TWCNoDataError("empty"),
        TWCAuthError("bad key for optional endpoint"),
        TWCPermissionError("no access"),
        TWCRequestError("temporary tropical failure"),
    ],
)
async def test_coordinator_keeps_weather_data_when_optional_tropical_unavailable(
    hass, error
) -> None:
    """Optional tropical endpoint failures should not fail weather refresh."""
    client = AsyncMock()
    client.async_get_current_conditions.return_value = {"temperature": 72}
    client.async_get_daily_forecast.return_value = {"temperatureMax": [75]}
    client.async_get_hourly_forecast.return_value = {"temperature": [72, 71]}
    client.async_get_alert_headlines.return_value = {"alerts": []}
    client.async_get_tropical_current_position.side_effect = error
    coordinator = TWCWeatherCoordinator(hass, client, tropical_enabled=True)

    data = await coordinator._async_update_data()

    assert data.current == {"temperature": 72}
    assert data.tropical_current_position == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        TWCNoDataError("empty"),
        TWCAuthError("bad key for optional endpoint"),
        TWCPermissionError("no access"),
        TWCRequestError("temporary air quality failure"),
    ],
)
async def test_coordinator_keeps_weather_data_when_optional_air_quality_unavailable(
    hass, error
) -> None:
    """Optional air quality endpoint failures should not fail weather refresh."""
    client = AsyncMock()
    client.async_get_current_conditions.return_value = {"temperature": 72}
    client.async_get_daily_forecast.return_value = {"temperatureMax": [75]}
    client.async_get_hourly_forecast.return_value = {"temperature": [72, 71]}
    client.async_get_alert_headlines.return_value = {"alerts": []}
    client.async_get_air_quality.side_effect = error
    coordinator = TWCWeatherCoordinator(hass, client, air_quality_enabled=True)

    data = await coordinator._async_update_data()

    assert data.current == {"temperature": 72}
    assert data.air_quality == {}


def test_coordinator_uses_configured_update_interval(hass) -> None:
    """Coordinator should use the configured polling interval."""
    client = AsyncMock()
    coordinator = TWCWeatherCoordinator(
        hass,
        client,
        update_interval=timedelta(minutes=15),
    )

    assert coordinator.update_interval == timedelta(minutes=15)


@pytest.mark.asyncio
async def test_coordinator_wraps_client_errors(hass) -> None:
    """Coordinator should surface TWC failures as UpdateFailed."""
    client = AsyncMock()
    client.async_get_current_conditions.side_effect = TWCRequestError("down")
    coordinator = TWCWeatherCoordinator(hass, client)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_raises_auth_failed_for_auth_errors(hass) -> None:
    """Coordinator should surface credential failures as config entry auth failures."""
    client = AsyncMock()
    client.async_get_current_conditions.side_effect = TWCAuthError("bad key")
    coordinator = TWCWeatherCoordinator(hass, client)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()
