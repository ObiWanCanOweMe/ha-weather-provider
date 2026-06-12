"""Tests for the HA Weather Provider coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.ha_weather_provider.api import TWCAuthError, TWCRequestError
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
    coordinator = TWCWeatherCoordinator(hass, client)

    data = await coordinator._async_update_data()

    assert data == TWCWeatherData(
        current={"temperature": 72},
        daily_forecast={"temperatureMax": [75]},
    )


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
