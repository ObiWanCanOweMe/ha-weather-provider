# TWC Client Library Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract TWC API access and reusable payload normalization out of the Home Assistant integration and into a small Python package inside this repo.

**Architecture:** Create a `twc_weather_client` package outside `custom_components` and move request execution, TWC exceptions, endpoint construction, and shared parsing helpers into it. Keep Home Assistant modules responsible for config entries, coordinators, entity classes, HA units, entity descriptions, and dashboard docs.

**Tech Stack:** Python 3.14, aiohttp, Home Assistant custom integration APIs, pytest, pytest-homeassistant-custom-component, aioresponses, ruff, obi-dev-harness.

---

### Task 1: Add Client Package Errors

**Files:**
- Create: `twc_weather_client/__init__.py`
- Create: `twc_weather_client/errors.py`
- Modify: `custom_components/ha_weather_provider/api.py`
- Test: `tests/test_twc_client_errors.py`

- [ ] **Step 1: Write the failing error export test**

Create `tests/test_twc_client_errors.py`:

```python
"""Tests for the standalone TWC client package exports."""

from twc_weather_client import (
    TWCAuthError,
    TWCError,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)


def test_twc_client_exports_errors() -> None:
    """The standalone package exposes all public TWC exceptions."""
    assert issubclass(TWCAuthError, TWCError)
    assert issubclass(TWCNoDataError, TWCError)
    assert issubclass(TWCPermissionError, TWCError)
    assert issubclass(TWCRequestError, TWCError)
```

- [ ] **Step 2: Run the failing test**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_twc_client_errors.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'twc_weather_client'`.

- [ ] **Step 3: Add package error classes**

Create `twc_weather_client/errors.py`:

```python
"""Errors raised by the The Weather Company client package."""

from __future__ import annotations


class TWCError(Exception):
    """Base error for TWC client failures."""


class TWCAuthError(TWCError):
    """TWC rejected the configured API key."""


class TWCPermissionError(TWCError):
    """TWC API key does not have access to the requested endpoint."""


class TWCNoDataError(TWCError):
    """TWC returned no data for the request."""


class TWCRequestError(TWCError):
    """TWC request failed."""
```

Create `twc_weather_client/__init__.py`:

```python
"""The Weather Company async client and payload helpers."""

from __future__ import annotations

from .errors import (
    TWCAuthError,
    TWCError,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)

__all__ = [
    "TWCAuthError",
    "TWCError",
    "TWCNoDataError",
    "TWCPermissionError",
    "TWCRequestError",
]
```

Update `custom_components/ha_weather_provider/api.py` to import these errors instead of defining them locally:

```python
from twc_weather_client import (
    TWCAuthError,
    TWCError,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)
```

Delete the local `TWCError`, `TWCAuthError`, `TWCPermissionError`, `TWCNoDataError`, and `TWCRequestError` class definitions from `custom_components/ha_weather_provider/api.py`.

- [ ] **Step 4: Run the error export test**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_twc_client_errors.py tests/test_api.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add twc_weather_client/__init__.py twc_weather_client/errors.py custom_components/ha_weather_provider/api.py tests/test_twc_client_errors.py
git commit -m "Extract TWC client errors"
```

### Task 2: Move Request Client Into Package

**Files:**
- Create: `twc_weather_client/client.py`
- Modify: `twc_weather_client/__init__.py`
- Modify: `custom_components/ha_weather_provider/api.py`
- Modify: `tests/test_api.py`
- Test: `tests/test_twc_client.py`

- [ ] **Step 1: Copy API tests to package-level client tests**

Create `tests/test_twc_client.py` by moving the API-client-only tests from `tests/test_api.py` into the new file. The first moved tests should cover current conditions and status mapping:

```python
"""Tests for the standalone TWC async client."""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from twc_weather_client import (
    TWCAuthError,
    TWCClient,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)
from twc_weather_client.client import BASE_URL, CURRENT_PATH


def _client(session: aiohttp.ClientSession) -> TWCClient:
    return TWCClient(
        session=session,
        api_key="api-key",
        latitude=33.931,
        longitude=-84.4677,
        units="e",
        language="en-US",
    )


@pytest.mark.asyncio
async def test_async_get_current_conditions_calls_twc_current_endpoint() -> None:
    """Current conditions use the documented observations endpoint."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            mocked.get(
                f"{BASE_URL}{CURRENT_PATH}",
                payload={"temperature": 71},
            )

            result = await _client(session).async_get_current_conditions()

    assert result == {"temperature": 71}
    request = mocked.requests[("GET", f"{BASE_URL}{CURRENT_PATH}")][0]
    assert request.kwargs["params"] == {
        "apiKey": "api-key",
        "geocode": "33.931,-84.4677",
        "units": "e",
        "language": "en-US",
        "format": "json",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (204, TWCNoDataError),
        (401, TWCAuthError),
        (403, TWCPermissionError),
        (500, TWCRequestError),
    ],
)
async def test_async_get_json_maps_twc_status_errors(
    status: int, error_type: type[Exception]
) -> None:
    """Documented TWC statuses map to stable client exceptions."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            mocked.get(f"{BASE_URL}{CURRENT_PATH}", status=status)

            with pytest.raises(error_type):
                await _client(session).async_get_current_conditions()
```

Leave integration-specific tests in `tests/test_api.py` temporarily. They will continue importing through the compatibility shim until this task finishes.

- [ ] **Step 2: Run the copied tests and verify import failure**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_twc_client.py -q`

Expected: FAIL with `ImportError` for `TWCClient` or `twc_weather_client.client`.

- [ ] **Step 3: Move the client implementation**

Create `twc_weather_client/client.py` by moving the current `TWCClient` implementation from `custom_components/ha_weather_provider/api.py`. Keep the method names and behavior unchanged.

Use this module header and imports:

```python
"""Async client for The Weather Company API."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
from aiohttp import ClientSession

from .errors import (
    TWCAuthError,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)

BASE_URL = "https://api.weather.com"
CURRENT_PATH = "/v3/wx/observations/current"
DAILY_FORECAST_PATH_PREFIX = "/v3/wx/forecast/daily"
HOURLY_FORECAST_PATH_PREFIX = "/v3/wx/forecast/hourly"
ALERT_HEADLINES_PATH = "/v3/alerts/headlines"
POLLEN_FORECAST_PATH_PREFIX = "/v2/indices/pollen/daypart"
POLLEN_OBSERVATION_PATH = "/v1/geocode/{latitude}/{longitude}/observations/pollen.json"
TROPICAL_CURRENT_POSITION_PATH = "/v2/tropical/currentposition"
AIR_QUALITY_PATH = "/v3/wx/globalAirQuality"
DEFAULT_DAILY_FORECAST_DURATION = "7day"
DEFAULT_HOURLY_FORECAST_DURATION = "2day"
DEFAULT_POLLEN_FORECAST_DURATION = "3day"
DEFAULT_AIR_QUALITY_SCALE = "EPA"
```

The constructor signature must remain:

```python
def __init__(
    self,
    *,
    session: ClientSession,
    api_key: str,
    latitude: float,
    longitude: float,
    units: str,
    language: str,
    daily_forecast_duration: str = DEFAULT_DAILY_FORECAST_DURATION,
    hourly_forecast_duration: str = DEFAULT_HOURLY_FORECAST_DURATION,
) -> None:
```

Keep `_async_get_json` and `_raise_for_status` behavior byte-for-byte equivalent except for imports.

- [ ] **Step 4: Export the client from the package**

Update `twc_weather_client/__init__.py`:

```python
"""The Weather Company async client and payload helpers."""

from __future__ import annotations

from .client import TWCClient
from .errors import (
    TWCAuthError,
    TWCError,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)

__all__ = [
    "TWCAuthError",
    "TWCClient",
    "TWCError",
    "TWCNoDataError",
    "TWCPermissionError",
    "TWCRequestError",
]
```

- [ ] **Step 5: Convert integration API module to a compatibility shim**

Replace `custom_components/ha_weather_provider/api.py` with:

```python
"""Compatibility imports for the standalone TWC client package."""

from __future__ import annotations

from twc_weather_client import (
    TWCAuthError,
    TWCClient,
    TWCError,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)

__all__ = [
    "TWCAuthError",
    "TWCClient",
    "TWCError",
    "TWCNoDataError",
    "TWCPermissionError",
    "TWCRequestError",
]
```

- [ ] **Step 6: Run client and compatibility tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_twc_client.py tests/test_api.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add twc_weather_client/__init__.py twc_weather_client/client.py custom_components/ha_weather_provider/api.py tests/test_twc_client.py tests/test_api.py
git commit -m "Move TWC request client into package"
```

### Task 3: Move Shared Normalizer Helpers

**Files:**
- Create: `twc_weather_client/normalizers.py`
- Modify: `twc_weather_client/__init__.py`
- Modify: `custom_components/ha_weather_provider/weather.py`
- Modify: `custom_components/ha_weather_provider/sensor.py`
- Test: `tests/test_twc_normalizers.py`
- Test: `tests/test_weather.py`
- Test: `tests/test_sensor.py`

- [ ] **Step 1: Write normalizer tests**

Create `tests/test_twc_normalizers.py`:

```python
"""Tests for reusable TWC payload normalization helpers."""

from __future__ import annotations

from twc_weather_client.normalizers import (
    alert_summaries,
    condition_from_twc,
    first_daypart_value,
    first_non_null,
    series_item,
    series_value,
    series_values,
    value,
)


def test_value_returns_none_for_empty_string() -> None:
    assert value({"windGust": ""}, "windGust") is None


def test_condition_from_twc_maps_icon_code() -> None:
    assert condition_from_twc(32, "Sunny") == "sunny"
    assert condition_from_twc(3, "Strong Thunderstorms") == "lightning-rainy"


def test_condition_from_twc_maps_phrase_without_icon() -> None:
    assert condition_from_twc(None, "Snow showers") == "snowy"
    assert condition_from_twc(None, "Partly cloudy") == "partlycloudy"


def test_series_helpers_reject_malformed_values() -> None:
    assert series_values("bad") == []
    assert series_item([1, True, "bad"], 0) == 1
    assert series_item([1, True, "bad"], 1) is None
    assert series_value({"items": ["", 3]}, "items", 0) is None
    assert series_value({"items": ["", 3]}, "items", 1) == 3


def test_first_daypart_value_handles_interlaced_daypart_arrays() -> None:
    daypart = {"wxPhraseLong": [None, "Sunny", "Clear", "Cloudy"]}

    assert first_daypart_value(daypart, "wxPhraseLong", 0) == "Sunny"
    assert first_daypart_value(daypart, "wxPhraseLong", 1) == "Cloudy"


def test_first_non_null_skips_empty_values() -> None:
    assert first_non_null(None, "", 5) == 5


def test_alert_summaries_returns_stable_shape() -> None:
    assert alert_summaries(
        {
            "alerts": [
                {
                    "detailKey": "key",
                    "eventDescription": "Flood Watch",
                    "headlineText": "Flooding possible",
                    "severity": "Moderate",
                    "severityCode": 3,
                    "urgency": "Future",
                    "certainty": "Possible",
                    "expireTimeLocal": "2026-06-16T20:00:00-04:00",
                    "source": "NWS",
                }
            ]
        }
    ) == [
        {
            "detail_key": "key",
            "event": "Flood Watch",
            "headline": "Flooding possible",
            "severity": "Moderate",
            "severity_code": 3,
            "urgency": "Future",
            "certainty": "Possible",
            "expires": "2026-06-16T20:00:00-04:00",
            "source": "NWS",
        }
    ]
```

- [ ] **Step 2: Run the failing normalizer tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_twc_normalizers.py -q`

Expected: FAIL with `ModuleNotFoundError` for `twc_weather_client.normalizers`.

- [ ] **Step 3: Add reusable normalizers**

Create `twc_weather_client/normalizers.py` by moving these helpers from `weather.py`:

```python
"""Reusable payload normalizers for The Weather Company responses."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

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


def value(data: dict[str, Any], key: str) -> Any:
    """Return a non-null value from a TWC payload."""
    raw_value = data.get(key)
    return None if raw_value == "" else raw_value


def condition_from_twc(
    icon_code: Any, phrase: str | None = None, *, daytime: bool | None = None
) -> str | None:
    """Map TWC icon code or phrase to a Home Assistant weather condition."""
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
        if daytime is True:
            return "sunny"
        return "clear-night"
    if "sun" in phrase:
        return "sunny"
    return None


def first_daypart_value(daypart: Any, key: str, index: int) -> Any:
    """Return the first daytime value for a daily forecast index."""
    if not isinstance(daypart, dict):
        return None
    values = daypart.get(key)
    if not isinstance(values, list) or not values:
        return None
    series = values[0] if len(values) == 1 and isinstance(values[0], list) else values
    if not isinstance(series, list) or not series:
        return None
    offset = index * 2 + (1 if series[0] is None else 0)
    if offset >= len(series):
        return None
    raw_value = series[offset]
    if isinstance(raw_value, list):
        return next((item for item in raw_value if item is not None), None)
    return raw_value


def forecast_datetime(valid_time: Any) -> str | None:
    """Convert a TWC epoch to an ISO timestamp, or skip invalid values."""
    if not isinstance(valid_time, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(valid_time, UTC).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def series_values(raw_value: Any) -> list[Any]:
    """Return a list-like forecast series, or an empty list for malformed input."""
    return raw_value if isinstance(raw_value, list) else []


def series_item(series: list[Any], index: int) -> Any:
    """Return a numeric item from a forecast series, or None for malformed values."""
    if index >= len(series):
        return None
    raw_value = series[index]
    return (
        raw_value
        if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool)
        else None
    )


def series_value(data: dict[str, Any], key: str, index: int) -> Any:
    """Return one non-empty forecast series value by index."""
    series = series_values(data.get(key))
    if index >= len(series):
        return None
    raw_value = series[index]
    return None if raw_value == "" else raw_value


def first_non_null(*values: Any) -> Any:
    """Return the first non-null, non-empty value."""
    return next((item for item in values if item is not None and item != ""), None)


def alert_summaries(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return stable alert headline summaries from a TWC alert payload."""
    alerts = data.get("alerts")
    if not isinstance(alerts, list):
        return []

    summaries: list[dict[str, Any]] = []
    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        summaries.append(
            {
                "detail_key": value(alert, "detailKey"),
                "event": value(alert, "eventDescription"),
                "headline": value(alert, "headlineText"),
                "severity": value(alert, "severity"),
                "severity_code": value(alert, "severityCode"),
                "urgency": value(alert, "urgency"),
                "certainty": value(alert, "certainty"),
                "expires": value(alert, "expireTimeLocal"),
                "source": value(alert, "source"),
            }
        )
    return summaries
```

- [ ] **Step 4: Export normalizers from the package**

Update `twc_weather_client/__init__.py`:

```python
from .normalizers import (
    alert_summaries,
    condition_from_twc,
    first_daypart_value,
    first_non_null,
    forecast_datetime,
    series_item,
    series_value,
    series_values,
    value,
)
```

Add these names to `__all__`:

```python
    "alert_summaries",
    "condition_from_twc",
    "first_daypart_value",
    "first_non_null",
    "forecast_datetime",
    "series_item",
    "series_value",
    "series_values",
    "value",
```

- [ ] **Step 5: Update weather entity imports**

Modify `custom_components/ha_weather_provider/weather.py`:

```python
from twc_weather_client import (
    alert_summaries as _alert_summaries,
    condition_from_twc as _condition,
    first_daypart_value as _first_daypart_value,
    first_non_null as _first_non_null,
    forecast_datetime as _forecast_datetime,
    series_item as _series_item,
    series_value as _series_value,
    series_values as _series_values,
    value as _value,
)
```

Remove local definitions for:

- `CONDITION_BY_ICON`
- `_value`
- `_condition`
- `_first_daypart_value`
- `_forecast_datetime`
- `_series_values`
- `_series_item`
- `_series_value`
- `_first_non_null`
- `_alert_summaries`

Keep `_forecast_high` in `weather.py` because it is specific to HA forecast dictionary mapping.

- [ ] **Step 6: Update sensor imports**

Modify `custom_components/ha_weather_provider/sensor.py`:

```python
from twc_weather_client import (
    condition_from_twc as _condition,
    first_daypart_value as _first_daypart_value,
    series_value as _series_value,
    series_values as _series_values,
    value as _value,
)
```

Remove the local `_value` helper from `sensor.py`.

Keep sensor-specific helpers in `sensor.py`, including pollen observation parsing, air quality sensor attributes, and daily adapter entity functions.

- [ ] **Step 7: Run normalizer and entity tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_twc_normalizers.py tests/test_weather.py tests/test_sensor.py -q`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add twc_weather_client/__init__.py twc_weather_client/normalizers.py custom_components/ha_weather_provider/weather.py custom_components/ha_weather_provider/sensor.py tests/test_twc_normalizers.py tests/test_weather.py tests/test_sensor.py
git commit -m "Extract TWC payload normalizers"
```

### Task 4: Point HA Coordinator At Package Client

**Files:**
- Modify: `custom_components/ha_weather_provider/coordinator.py`
- Modify: `custom_components/ha_weather_provider/__init__.py`
- Modify: `tests/test_coordinator.py`
- Modify: `tests/test_init.py`

- [ ] **Step 1: Update imports away from compatibility shim**

Modify `custom_components/ha_weather_provider/coordinator.py`:

```python
from twc_weather_client import (
    TWCAuthError,
    TWCClient,
    TWCError,
    TWCNoDataError,
    TWCPermissionError,
)
```

Modify `custom_components/ha_weather_provider/__init__.py`:

```python
from twc_weather_client import TWCAuthError, TWCClient, TWCPermissionError
```

Remove imports from `.api` in both files.

- [ ] **Step 2: Run setup and coordinator tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_init.py tests/test_coordinator.py -q`

Expected: PASS.

- [ ] **Step 3: Delete the compatibility shim if no imports remain**

Run: `rg "ha_weather_provider\\.api|from \\.api|import \\.api" custom_components tests`

Expected: no output except tests that intentionally verify compatibility. If no imports remain, delete `custom_components/ha_weather_provider/api.py` and move remaining tests from `tests/test_api.py` into `tests/test_twc_client.py`.

After deleting the file, run:

`PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_twc_client.py tests/test_init.py tests/test_coordinator.py -q`

Expected: PASS.

- [ ] **Step 4: Commit**

If `api.py` was deleted:

```bash
git add custom_components/ha_weather_provider/__init__.py custom_components/ha_weather_provider/coordinator.py custom_components/ha_weather_provider/api.py tests/test_twc_client.py tests/test_api.py tests/test_init.py tests/test_coordinator.py
git commit -m "Use standalone TWC client in HA integration"
```

If `api.py` remains as a shim because tests or external imports still need it:

```bash
git add custom_components/ha_weather_provider/__init__.py custom_components/ha_weather_provider/coordinator.py custom_components/ha_weather_provider/api.py tests/test_twc_client.py tests/test_api.py tests/test_init.py tests/test_coordinator.py
git commit -m "Use standalone TWC client in HA integration"
```

### Task 5: Final Verification

**Files:**
- Modify: no files unless verification exposes a defect

- [ ] **Step 1: Run Ruff**

Run: `.worktrees/demo-dashboard-card/.venv/bin/ruff check twc_weather_client custom_components/ha_weather_provider tests`

Expected: PASS.

- [ ] **Step 2: Run full project checks**

Run: `PATH=".worktrees/demo-dashboard-card/.venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .`

Expected: compile, JSON validation, Ruff/harness checks, and pytest all pass.

- [ ] **Step 3: Commit any verification fixes**

If verification required fixes:

```bash
git add twc_weather_client custom_components/ha_weather_provider tests
git commit -m "Stabilize TWC client package extraction"
```

If no fixes were needed, do not create an empty commit.

- [ ] **Step 4: Push branch**

```bash
git push origin twc-client-library-boundary
```

Expected: branch is pushed and ready for a GitLab MR into `master`.
