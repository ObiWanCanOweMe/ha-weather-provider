# TWC Weather Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a functional Home Assistant custom weather integration backed by The Weather Company current conditions and 7-day daily forecast APIs.

**Architecture:** Add a focused async TWC API client, a `DataUpdateCoordinator` that fetches current and daily forecast data together, and a `WeatherEntity` that maps cached coordinator data into Home Assistant weather properties. Keep validation, API transport, data mapping, and entity behavior separated so hourly forecast can be added later without rewriting the first version.

**Tech Stack:** Python, Home Assistant custom integration APIs, aiohttp via `async_get_clientsession`, `DataUpdateCoordinator`, pytest, pytest-homeassistant-custom-component, aioresponses.

---

## File Structure

- Create `.gitignore`: ignore Python caches, pytest caches, virtualenvs, coverage output, and local env files.
- Create `requirements-dev.txt`: development/test dependencies for this standalone custom integration repo.
- Create `pytest.ini`: pytest configuration for async tests.
- Create `tests/conftest.py`: Home Assistant custom integration test fixtures.
- Create `tests/test_api.py`: unit tests for TWC URL construction and HTTP error mapping.
- Create `tests/test_config_flow.py`: config flow validation and entry creation tests.
- Create `tests/test_coordinator.py`: coordinator data merge and failure behavior tests.
- Create `tests/test_weather.py`: entity property and forecast mapping tests.
- Create `custom_components/ha_weather_provider/api.py`: async TWC API client and integration-specific exceptions.
- Create `custom_components/ha_weather_provider/coordinator.py`: coordinator and combined data model.
- Modify `custom_components/ha_weather_provider/const.py`: config keys, defaults, unit mappings, update interval.
- Modify `custom_components/ha_weather_provider/config_flow.py`: collect API key, latitude, longitude, units, and language; validate against TWC.
- Modify `custom_components/ha_weather_provider/__init__.py`: create client/coordinator during setup and store runtime data.
- Modify `custom_components/ha_weather_provider/weather.py`: implement coordinator-backed weather entity and daily forecast API.
- Modify `custom_components/ha_weather_provider/strings.json` and `translations/en.json`: update config flow fields and errors.
- Modify `custom_components/ha_weather_provider/manifest.json`: replace the temporary documentation URL with the GitLab project URL.
- Modify `.codex-harness.yml`: add pytest check once the test harness exists.

## Reference Notes

- Home Assistant weather entity properties must return memory-only values and use `async_forecast_daily` when `WeatherEntityFeature.FORECAST_DAILY` is set.
- Home Assistant forecast data is no longer part of weather entity state; cache it and return it from the forecast method.
- Home Assistant recommends `DataUpdateCoordinator` for coordinated polling of API data.
- TWC requests use `https://api.weather.com`, `geocode=lat,lon`, `units=e|m|h|s`, `language`, `format=json`, and `apiKey`.
- TWC v2/v3 `204`, `401`, `403`, `406`, `408`, and `5xx` responses need explicit handling.

---

### Task 1: Add Local Test Harness

**Files:**
- Create: `.gitignore`
- Create: `requirements-dev.txt`
- Create: `pytest.ini`
- Create: `tests/conftest.py`
- Modify: `.codex-harness.yml`

- [ ] **Step 1: Add repository ignore rules**

Write `.gitignore`:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
.venv/
venv/
.env
```

- [ ] **Step 2: Add development dependencies**

Write `requirements-dev.txt`:

```text
homeassistant
pytest
pytest-asyncio
pytest-homeassistant-custom-component
aioresponses
ruff
```

- [ ] **Step 3: Add pytest configuration**

Write `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 4: Add Home Assistant test fixtures**

Write `tests/conftest.py`:

```python
"""Shared test fixtures for HA Weather Provider."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in Home Assistant tests."""
    yield
```

- [ ] **Step 5: Add pytest to harness checks**

Update `.codex-harness.yml` so `checks` includes pytest after the JSON checks:

```yaml
kind: home-assistant-custom-integration
checks:
  - python3 -m compileall custom_components/ha_weather_provider
  - python3 -m json.tool custom_components/ha_weather_provider/manifest.json
  - python3 -m json.tool custom_components/ha_weather_provider/strings.json
  - python3 -m json.tool custom_components/ha_weather_provider/translations/en.json
  - python3 -m pytest
smoke:
  - python3 -m compileall custom_components/ha_weather_provider
gitlab:
  host: git.kener.org
  namespace: my-projects
  project: ha-weather-provider
  path: my-projects/ha-weather-provider
milestones:
  - Hourly Forecast
```

- [ ] **Step 6: Install dependencies**

Run:

```bash
python3 -m pip install -r requirements-dev.txt
```

Expected: dependencies install successfully. If Home Assistant dependency resolution is slow, keep the command running rather than replacing the test stack.

- [ ] **Step 7: Run empty test suite**

Run:

```bash
python3 -m pytest
```

Expected: pytest starts successfully and reports no tests collected or passes the fixture import.

- [ ] **Step 8: Commit**

```bash
git add .gitignore requirements-dev.txt pytest.ini tests/conftest.py .codex-harness.yml
git commit -m "test: add Home Assistant test harness"
```

---

### Task 2: Add Constants and Config Flow Validation

**Files:**
- Modify: `custom_components/ha_weather_provider/const.py`
- Modify: `custom_components/ha_weather_provider/config_flow.py`
- Modify: `custom_components/ha_weather_provider/strings.json`
- Modify: `custom_components/ha_weather_provider/translations/en.json`
- Test: `tests/test_config_flow.py`

- [ ] **Step 1: Write failing config flow tests**

Write `tests/test_config_flow.py`:

```python
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
    """Valid user input creates one config entry."""
    with patch(
        "custom_components.ha_weather_provider.config_flow.TWCClient"
    ) as client_cls:
        client = client_cls.return_value
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
    """Out-of-range coordinates show a form error."""
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
    """Authentication failures are surfaced to the user."""
    from custom_components.ha_weather_provider.api import TWCAuthError

    with patch(
        "custom_components.ha_weather_provider.config_flow.TWCClient"
    ) as client_cls:
        client = client_cls.return_value
        client.async_get_current_conditions = AsyncMock(side_effect=TWCAuthError("bad key"))

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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_config_flow.py -v
```

Expected: FAIL because `CONF_LANGUAGE`, `CONF_LATITUDE`, `CONF_LONGITUDE`, `CONF_UNITS`, and `api.TWCClient` are not defined yet.

- [ ] **Step 3: Add config constants**

Replace `custom_components/ha_weather_provider/const.py` with:

```python
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
        "pressure": UnitOfPressure.MBAR,
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
        "pressure": UnitOfPressure.MBAR,
        "speed": UnitOfSpeed.METERS_PER_SECOND,
        "precipitation": UnitOfLength.MILLIMETERS,
        "visibility": UnitOfLength.KILOMETERS,
    },
}
```

- [ ] **Step 4: Add temporary API exception stubs**

Create `custom_components/ha_weather_provider/api.py`:

```python
"""Client for The Weather Company APIs."""

from __future__ import annotations


class TWCError(Exception):
    """Base TWC API error."""


class TWCAuthError(TWCError):
    """TWC rejected the configured API key."""


class TWCPermissionError(TWCError):
    """TWC API key does not have access to the requested endpoint."""


class TWCNoDataError(TWCError):
    """TWC returned no data for the request."""


class TWCRequestError(TWCError):
    """TWC request failed."""


class TWCClient:
    """Temporary TWC client shell; completed in the API client task."""

    async def async_get_current_conditions(self) -> dict:
        """Return current conditions."""
        raise NotImplementedError
```

- [ ] **Step 5: Update config flow implementation**

Replace `custom_components/ha_weather_provider/config_flow.py` with:

```python
"""Config flow for HA Weather Provider."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TWCAuthError, TWCClient, TWCError, TWCPermissionError
from .const import (
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_UNITS,
    DEFAULT_LANGUAGE,
    DEFAULT_UNITS,
    DOMAIN,
    TWC_UNITS,
)


def _validate_coordinates(latitude: float, longitude: float) -> bool:
    """Return whether coordinates are valid WGS84 latitude/longitude."""
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


class HAWeatherProviderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Weather Provider."""

    VERSION = 1

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
                        title=f"TWC Weather {latitude:.4f},{longitude:.4f}",
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
```

- [ ] **Step 6: Update config flow strings**

Replace both `custom_components/ha_weather_provider/strings.json` and `custom_components/ha_weather_provider/translations/en.json` with:

```json
{
  "config": {
    "step": {
      "user": {
        "title": "HA Weather Provider",
        "description": "Set up The Weather Company weather data.",
        "data": {
          "api_key": "API Key",
          "latitude": "Latitude",
          "longitude": "Longitude",
          "units": "Units",
          "language": "Language"
        }
      }
    },
    "error": {
      "cannot_connect": "Failed to connect to The Weather Company API.",
      "invalid_auth": "The API key was rejected.",
      "not_authorized": "The API key is not authorized for this Weather Company endpoint.",
      "invalid_coordinates": "Latitude or longitude is outside the supported range.",
      "invalid_units": "The selected unit system is not supported."
    }
  }
}
```

- [ ] **Step 7: Run config flow tests**

Run:

```bash
python3 -m pytest tests/test_config_flow.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add custom_components/ha_weather_provider/const.py custom_components/ha_weather_provider/api.py custom_components/ha_weather_provider/config_flow.py custom_components/ha_weather_provider/strings.json custom_components/ha_weather_provider/translations/en.json tests/test_config_flow.py
git commit -m "feat: collect TWC configuration"
```

---

### Task 3: Implement TWC API Client

**Files:**
- Modify: `custom_components/ha_weather_provider/api.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write failing API client tests**

Write `tests/test_api.py`:

```python
"""Tests for The Weather Company API client."""

from __future__ import annotations

from aiohttp import ClientSession
from aioresponses import aioresponses
import pytest

from custom_components.ha_weather_provider.api import (
    TWCAuthError,
    TWCClient,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)


def _client(session: ClientSession) -> TWCClient:
    return TWCClient(
        session=session,
        api_key="secret",
        latitude=40.58,
        longitude=-111.66,
        units="e",
        language="en-US",
    )


async def test_get_current_conditions_builds_request():
    """Current conditions request uses the expected TWC endpoint and params."""
    async with ClientSession() as session:
        client = _client(session)
        with aioresponses() as mocked:
            mocked.get(
                "https://api.weather.com/v3/wx/observations/current",
                payload={"temperature": 72},
                status=200,
            )
            data = await client.async_get_current_conditions()

            request = next(iter(mocked.requests.values()))[0]

    assert data == {"temperature": 72}
    assert request.kwargs["params"] == {
        "apiKey": "secret",
        "geocode": "40.58,-111.66",
        "units": "e",
        "language": "en-US",
        "format": "json",
    }
    assert request.kwargs["headers"]["Accept-Encoding"] == "gzip"


async def test_get_daily_forecast_builds_request():
    """Daily forecast request uses the 7-day endpoint."""
    async with ClientSession() as session:
        client = _client(session)
        with aioresponses() as mocked:
            mocked.get(
                "https://api.weather.com/v3/wx/forecast/daily/7day",
                payload={"dayOfWeek": ["Monday"]},
                status=200,
            )
            data = await client.async_get_daily_forecast()

    assert data == {"dayOfWeek": ["Monday"]}


@pytest.mark.parametrize(
    ("status", "exc_type"),
    [
        (204, TWCNoDataError),
        (401, TWCAuthError),
        (403, TWCPermissionError),
        (500, TWCRequestError),
        (503, TWCRequestError),
    ],
)
async def test_error_mapping(status: int, exc_type: type[Exception]):
    """HTTP statuses are mapped into integration-specific exceptions."""
    async with ClientSession() as session:
        client = _client(session)
        with aioresponses() as mocked:
            mocked.get(
                "https://api.weather.com/v3/wx/observations/current",
                status=status,
            )
            with pytest.raises(exc_type):
                await client.async_get_current_conditions()
```

- [ ] **Step 2: Run API tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_api.py -v
```

Expected: FAIL because `TWCClient.__init__`, `async_get_daily_forecast`, and HTTP behavior are not implemented.

- [ ] **Step 3: Implement API client**

Replace `custom_components/ha_weather_provider/api.py` with:

```python
"""Client for The Weather Company APIs."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession

BASE_URL = "https://api.weather.com"
CURRENT_PATH = "/v3/wx/observations/current"
DAILY_FORECAST_PATH = "/v3/wx/forecast/daily/7day"


class TWCError(Exception):
    """Base TWC API error."""


class TWCAuthError(TWCError):
    """TWC rejected the configured API key."""


class TWCPermissionError(TWCError):
    """TWC API key does not have access to the requested endpoint."""


class TWCNoDataError(TWCError):
    """TWC returned no data for the request."""


class TWCRequestError(TWCError):
    """TWC request failed."""


class TWCClient:
    """Async client for The Weather Company APIs."""

    def __init__(
        self,
        *,
        session: ClientSession,
        api_key: str,
        latitude: float,
        longitude: float,
        units: str,
        language: str,
    ) -> None:
        self._session = session
        self._api_key = api_key
        self._latitude = latitude
        self._longitude = longitude
        self._units = units
        self._language = language

    @property
    def _query_params(self) -> dict[str, str]:
        return {
            "apiKey": self._api_key,
            "geocode": f"{self._latitude},{self._longitude}",
            "units": self._units,
            "language": self._language,
            "format": "json",
        }

    async def async_get_current_conditions(self) -> dict[str, Any]:
        """Return current conditions."""
        return await self._async_get_json(CURRENT_PATH)

    async def async_get_daily_forecast(self) -> dict[str, Any]:
        """Return 7-day daily forecast."""
        return await self._async_get_json(DAILY_FORECAST_PATH)

    async def _async_get_json(self, path: str) -> dict[str, Any]:
        """Fetch a TWC JSON endpoint."""
        url = f"{BASE_URL}{path}"
        try:
            response = await self._session.get(
                url,
                params=self._query_params,
                headers={"Accept-Encoding": "gzip"},
            )
        except ClientError as err:
            raise TWCRequestError("TWC request failed") from err

        async with response:
            await self._raise_for_status(response)
            data = await response.json()

        if not isinstance(data, dict):
            raise TWCRequestError("TWC response was not a JSON object")
        return data

    async def _raise_for_status(self, response: ClientResponse) -> None:
        """Map TWC HTTP statuses to integration exceptions."""
        status = response.status
        if status == 200:
            return
        if status == 204:
            raise TWCNoDataError("No TWC data found for location")
        if status == 401:
            raise TWCAuthError("TWC API key rejected")
        if status == 403:
            raise TWCPermissionError("TWC API key is not authorized")
        if status in {400, 404, 405, 406, 408, 500, 502, 503, 504}:
            raise TWCRequestError(f"TWC request failed with HTTP {status}")
        raise TWCRequestError(f"Unexpected TWC HTTP status {status}")
```

- [ ] **Step 4: Run API tests**

Run:

```bash
python3 -m pytest tests/test_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Run config flow tests**

Run:

```bash
python3 -m pytest tests/test_config_flow.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/ha_weather_provider/api.py tests/test_api.py
git commit -m "feat: add TWC API client"
```

---

### Task 4: Add Coordinator and Runtime Setup

**Files:**
- Create: `custom_components/ha_weather_provider/coordinator.py`
- Modify: `custom_components/ha_weather_provider/__init__.py`
- Modify: `custom_components/ha_weather_provider/weather.py`
- Test: `tests/test_coordinator.py`

- [ ] **Step 1: Write failing coordinator tests**

Write `tests/test_coordinator.py`:

```python
"""Tests for HA Weather Provider coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.ha_weather_provider.api import TWCRequestError
from custom_components.ha_weather_provider.coordinator import (
    TWCWeatherCoordinator,
    TWCWeatherData,
)


async def test_coordinator_combines_current_and_forecast(hass):
    """Coordinator merges current conditions and daily forecast payloads."""
    client = AsyncMock()
    client.async_get_current_conditions.return_value = {"temperature": 72}
    client.async_get_daily_forecast.return_value = {"temperatureMax": [75]}

    coordinator = TWCWeatherCoordinator(hass, client)
    data = await coordinator._async_update_data()

    assert data == TWCWeatherData(
        current={"temperature": 72},
        daily_forecast={"temperatureMax": [75]},
    )


async def test_coordinator_wraps_client_errors(hass):
    """Coordinator raises UpdateFailed for TWC request errors."""
    client = AsyncMock()
    client.async_get_current_conditions.side_effect = TWCRequestError("down")

    coordinator = TWCWeatherCoordinator(hass, client)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
```

- [ ] **Step 2: Run coordinator tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_coordinator.py -v
```

Expected: FAIL because `coordinator.py` does not exist.

- [ ] **Step 3: Implement coordinator**

Write `custom_components/ha_weather_provider/coordinator.py`:

```python
"""Data update coordinator for HA Weather Provider."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TWCClient, TWCError
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class TWCWeatherData:
    """Combined TWC weather payloads."""

    current: dict[str, Any]
    daily_forecast: dict[str, Any]


class TWCWeatherCoordinator(DataUpdateCoordinator[TWCWeatherData]):
    """Coordinate TWC weather data refreshes."""

    def __init__(self, hass: HomeAssistant, client: TWCClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_UPDATE_INTERVAL,
            always_update=False,
        )
        self.client = client

    async def _async_update_data(self) -> TWCWeatherData:
        """Fetch current conditions and 7-day daily forecast."""
        try:
            current = await self.client.async_get_current_conditions()
            daily_forecast = await self.client.async_get_daily_forecast()
        except TWCError as err:
            raise UpdateFailed(str(err)) from err

        return TWCWeatherData(current=current, daily_forecast=daily_forecast)
```

- [ ] **Step 4: Update setup to create client and coordinator**

Replace `custom_components/ha_weather_provider/__init__.py` with:

```python
"""The HA Weather Provider integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TWCClient
from .const import (
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_UNITS,
    DOMAIN,
)
from .coordinator import TWCWeatherCoordinator

PLATFORMS: list[str] = ["weather"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Weather Provider from a config entry."""
    session = async_get_clientsession(hass)
    client = TWCClient(
        session=session,
        api_key=entry.data[CONF_API_KEY],
        latitude=entry.data[CONF_LATITUDE],
        longitude=entry.data[CONF_LONGITUDE],
        units=entry.data[CONF_UNITS],
        language=entry.data[CONF_LANGUAGE],
    )
    coordinator = TWCWeatherCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
```

- [ ] **Step 5: Temporarily adapt weather platform to coordinator storage**

Replace `custom_components/ha_weather_provider/weather.py` with:

```python
"""Weather platform for HA Weather Provider."""

from __future__ import annotations

from homeassistant.components.weather import WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TWCWeatherCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the weather entity from a config entry."""
    coordinator: TWCWeatherCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HAWeatherProviderEntity(coordinator, entry)])


class HAWeatherProviderEntity(CoordinatorEntity[TWCWeatherCoordinator], WeatherEntity):
    """Representation of a TWC weather entity."""

    def __init__(self, coordinator: TWCWeatherCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = entry.title
        self._attr_unique_id = entry.entry_id
```

- [ ] **Step 6: Run coordinator tests**

Run:

```bash
python3 -m pytest tests/test_coordinator.py -v
```

Expected: PASS.

- [ ] **Step 7: Run all current tests**

Run:

```bash
python3 -m pytest tests/test_api.py tests/test_config_flow.py tests/test_coordinator.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add custom_components/ha_weather_provider/__init__.py custom_components/ha_weather_provider/coordinator.py custom_components/ha_weather_provider/weather.py tests/test_coordinator.py
git commit -m "feat: coordinate TWC weather updates"
```

---

### Task 5: Implement Weather Entity Mapping

**Files:**
- Modify: `custom_components/ha_weather_provider/weather.py`
- Test: `tests/test_weather.py`

- [ ] **Step 1: Write failing weather entity tests**

Write `tests/test_weather.py`:

```python
"""Tests for TWC weather entity mapping."""

from __future__ import annotations

from types import SimpleNamespace

from homeassistant.components.weather import WeatherEntityFeature

from custom_components.ha_weather_provider.const import (
    CONF_UNITS,
    UNIT_SYSTEMS,
)
from custom_components.ha_weather_provider.coordinator import TWCWeatherData
from custom_components.ha_weather_provider.weather import HAWeatherProviderEntity


def _entity() -> HAWeatherProviderEntity:
    coordinator = SimpleNamespace(
        data=TWCWeatherData(
            current={
                "temperature": 72,
                "temperatureFeelsLike": 73,
                "relativeHumidity": 54,
                "pressureMeanSeaLevel": 30.12,
                "windSpeed": 7,
                "windGust": 12,
                "windDirection": 220,
                "visibility": 10,
                "uvIndex": 6,
                "wxPhraseLong": "Partly Cloudy",
                "iconCode": 30,
            },
            daily_forecast={
                "validTimeUtc": [1718121600],
                "temperatureMax": [78],
                "temperatureMin": [61],
                "narrative": ["Partly cloudy."],
                "daypart": [
                    {
                        "wxPhraseLong": [["Partly Cloudy", "Mostly Clear"]],
                        "iconCode": [[30, 33]],
                        "precipChance": [[15, 5]],
                        "windSpeed": [[8, 4]],
                        "windDirection": [[210, 190]],
                    }
                ],
            },
        )
    )
    entry = SimpleNamespace(
        title="TWC Weather 40.5800,-111.6600",
        entry_id="abc123",
        data={CONF_UNITS: "e"},
    )
    return HAWeatherProviderEntity(coordinator, entry)


def test_current_properties_map_twc_data():
    """Entity exposes current TWC values in native units."""
    entity = _entity()

    assert entity.supported_features == WeatherEntityFeature.FORECAST_DAILY
    assert entity.native_temperature == 72
    assert entity.native_apparent_temperature == 73
    assert entity.humidity == 54
    assert entity.native_pressure == 30.12
    assert entity.native_wind_speed == 7
    assert entity.native_wind_gust_speed == 12
    assert entity.wind_bearing == 220
    assert entity.native_visibility == 10
    assert entity.uv_index == 6
    assert entity.condition == "partlycloudy"
    assert entity.native_temperature_unit == UNIT_SYSTEMS["e"]["temperature"]


async def test_daily_forecast_maps_twc_data():
    """Entity returns Home Assistant daily forecast dictionaries."""
    forecast = await _entity().async_forecast_daily()

    assert forecast == [
        {
            "datetime": "2024-06-11T13:20:00+00:00",
            "condition": "partlycloudy",
            "native_temperature": 78,
            "native_templow": 61,
            "precipitation_probability": 15,
            "native_wind_speed": 8,
            "wind_bearing": 210,
        }
    ]
```

- [ ] **Step 2: Run weather tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_weather.py -v
```

Expected: FAIL because properties and forecast mapping are not implemented.

- [ ] **Step 3: Implement weather mapping**

Replace `custom_components/ha_weather_provider/weather.py` with:

```python
"""Weather platform for HA Weather Provider."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.weather import Forecast, WeatherEntity, WeatherEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_UNITS, DOMAIN, UNIT_SYSTEMS
from .coordinator import TWCWeatherCoordinator

CONDITION_BY_ICON = {
    0: "exceptional",
    1: "exceptional",
    2: "exceptional",
    3: "lightning-rainy",
    4: "lightning-rainy",
    5: "snowy-rainy",
    6: "snowy-rainy",
    7: "snowy-rainy",
    8: "snowy-rainy",
    9: "rainy",
    10: "snowy-rainy",
    11: "rainy",
    12: "rainy",
    13: "snowy",
    14: "snowy",
    15: "snowy",
    16: "snowy",
    17: "hail",
    18: "snowy-rainy",
    19: "fog",
    20: "fog",
    21: "fog",
    22: "fog",
    23: "windy",
    24: "windy",
    25: "exceptional",
    26: "cloudy",
    27: "partlycloudy",
    28: "partlycloudy",
    29: "partlycloudy",
    30: "partlycloudy",
    31: "clear-night",
    32: "sunny",
    33: "clear-night",
    34: "sunny",
    35: "hail",
    36: "sunny",
    37: "lightning",
    38: "lightning",
    39: "rainy",
    40: "rainy",
    41: "snowy",
    42: "snowy",
    43: "snowy",
    44: "partlycloudy",
    45: "lightning-rainy",
    46: "snowy",
    47: "lightning-rainy",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the weather entity from a config entry."""
    coordinator: TWCWeatherCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HAWeatherProviderEntity(coordinator, entry)])


def _value(data: dict[str, Any], key: str) -> Any:
    """Return a non-null value from a TWC payload."""
    value = data.get(key)
    return None if value == "" else value


def _condition(icon_code: Any, phrase: str | None = None) -> str | None:
    """Map TWC icon code or phrase to a Home Assistant condition."""
    if isinstance(icon_code, int) and icon_code in CONDITION_BY_ICON:
        return CONDITION_BY_ICON[icon_code]
    phrase = (phrase or "").lower()
    if "thunder" in phrase:
        return "lightning-rainy" if "rain" in phrase else "lightning"
    if "snow" in phrase:
        return "snowy-rainy" if "rain" in phrase else "snowy"
    if "rain" in phrase or "shower" in phrase:
        return "rainy"
    if "fog" in phrase or "mist" in phrase:
        return "fog"
    if "cloud" in phrase:
        return "partlycloudy" if "partly" in phrase or "mostly" in phrase else "cloudy"
    if "clear" in phrase:
        return "clear-night"
    if "sun" in phrase:
        return "sunny"
    return None


def _first_daypart_value(daypart: dict[str, Any], key: str, index: int) -> Any:
    """Return the first daytime value for a daily forecast index."""
    values = daypart.get(key) or []
    if not values:
        return None
    day_values = values[0]
    if index >= len(day_values):
        return None
    pair = day_values[index]
    if isinstance(pair, list):
        return next((item for item in pair if item is not None), None)
    return pair


class HAWeatherProviderEntity(CoordinatorEntity[TWCWeatherCoordinator], WeatherEntity):
    """Representation of a TWC weather entity."""

    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, coordinator: TWCWeatherCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = entry.title
        self._attr_unique_id = entry.entry_id
        self._units = UNIT_SYSTEMS[entry.data[CONF_UNITS]]

    @property
    def current(self) -> dict[str, Any]:
        """Return current TWC conditions."""
        return self.coordinator.data.current

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
    def condition(self) -> str | None:
        return _condition(_value(self.current, "iconCode"), _value(self.current, "wxPhraseLong"))

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        data = self.coordinator.data.daily_forecast
        valid_times = data.get("validTimeUtc") or []
        highs = data.get("temperatureMax") or []
        lows = data.get("temperatureMin") or []
        dayparts = data.get("daypart") or [{}]
        daypart = dayparts[0] if dayparts else {}

        forecasts: list[Forecast] = []
        for index, valid_time in enumerate(valid_times):
            forecast: Forecast = {
                "datetime": datetime.fromtimestamp(valid_time, UTC).isoformat(),
                "condition": _condition(
                    _first_daypart_value(daypart, "iconCode", index),
                    _first_daypart_value(daypart, "wxPhraseLong", index),
                ),
                "native_temperature": highs[index] if index < len(highs) else None,
                "native_templow": lows[index] if index < len(lows) else None,
                "precipitation_probability": _first_daypart_value(daypart, "precipChance", index),
                "native_wind_speed": _first_daypart_value(daypart, "windSpeed", index),
                "wind_bearing": _first_daypart_value(daypart, "windDirection", index),
            }
            forecasts.append({key: value for key, value in forecast.items() if value is not None})

        return forecasts
```

- [ ] **Step 4: Run weather tests**

Run:

```bash
python3 -m pytest tests/test_weather.py -v
```

Expected: PASS.

- [ ] **Step 5: Run all tests**

Run:

```bash
python3 -m pytest -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/ha_weather_provider/weather.py tests/test_weather.py
git commit -m "feat: expose TWC weather entity data"
```

---

### Task 6: Manifest, Documentation URL, and Full Verification

**Files:**
- Modify: `custom_components/ha_weather_provider/manifest.json`
- Modify: `docs/superpowers/specs/2026-06-12-twc-weather-integration-design.md` if implementation decisions discovered during coding need to be recorded.

- [ ] **Step 1: Update manifest documentation URL**

Replace `custom_components/ha_weather_provider/manifest.json` with:

```json
{
  "domain": "ha_weather_provider",
  "name": "HA Weather Provider",
  "version": "0.1.0",
  "config_flow": true,
  "documentation": "https://git.kener.org/my-projects/ha-weather-provider",
  "requirements": [],
  "codeowners": []
}
```

- [ ] **Step 2: Run all project checks**

Run:

```bash
python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .
```

Expected: compileall, JSON validation, and pytest all pass.

- [ ] **Step 3: Remove generated bytecode caches**

Run:

```bash
find custom_components tests -type d -name __pycache__ -prune -exec rm -rf {} +
```

Expected: no output.

- [ ] **Step 4: Verify clean status except intended manifest/spec edits**

Run:

```bash
git status --short
```

Expected: only intended tracked modifications are shown.

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha_weather_provider/manifest.json docs/superpowers/specs/2026-06-12-twc-weather-integration-design.md
git commit -m "chore: finalize TWC integration metadata"
```

If the spec file did not change, run:

```bash
git add custom_components/ha_weather_provider/manifest.json
git commit -m "chore: finalize TWC integration metadata"
```

- [ ] **Step 6: Push implementation branch**

Run:

```bash
git push
```

Expected: commits push to `origin/master`.

---

## Self-Review

Spec coverage:

- Config flow for API key, latitude, longitude, units, and language is covered in Task 2.
- Current conditions and 7-day daily forecast API access is covered in Task 3.
- Coordinator-based polling is covered in Task 4.
- Weather entity current properties and `async_forecast_daily` are covered in Task 5.
- Error handling for TWC HTTP statuses is covered in Task 3.
- Tests for config validation, client behavior, coordinator behavior, and entity mapping are covered in Tasks 2 through 5.
- GitLab milestone for hourly forecast has already been created and remains recorded in `.codex-harness.yml`.

Placeholder scan:

- The plan intentionally contains no incomplete markers or unspecified "add tests" instructions.
- Every code-changing step includes exact file paths and concrete code.

Type consistency:

- Config constants are introduced before they are consumed.
- `TWCClient`, `TWCWeatherCoordinator`, and `TWCWeatherData` signatures match their later usage.
- The weather entity reads the same `TWCWeatherData` fields produced by the coordinator.
