# HA Integration Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the Home Assistant integration layer with the best-practice recommendations after the TWC client package boundary has landed.

**Architecture:** Keep TWC HTTP and payload parsing in `twc_weather_client`; harden only the Home Assistant layer. Add integration metadata, diagnostics redaction, consistent optional endpoint behavior, operational docs, and repository hygiene checks.

**Tech Stack:** Home Assistant custom integration APIs, diagnostics platform, DataUpdateCoordinator, pytest, pytest-homeassistant-custom-component, ruff, obi-dev-harness.

---

## Additional Reference

Use `ludeeus/integration_blueprint` as a custom-integration layout reference during this plan. The relevant patterns are:

- Keep integration runtime code under `custom_components/<domain>`.
- Include manifest metadata such as `codeowners`, `documentation`, `iot_class`, `issue_tracker`, and `version`.
- Add `hacs.json` with minimum Home Assistant and HACS compatibility metadata when targeting HACS distribution.
- Keep a local development script that can start Home Assistant with `PYTHONPATH=custom_components`.
- Document installation, configuration, contribution, release, and HACS expectations in repo-level docs.

## Prerequisite

Run this plan only after `docs/superpowers/plans/2026-06-16-twc-client-library-boundary.md` is implemented, merged into `master`, and pulled locally.

Start from a clean branch:

```bash
git checkout master
git pull --ff-only origin master
git checkout -b ha-integration-hardening
```

Expected: branch `ha-integration-hardening` starts from the merged client-boundary work.

### Task 1: Add Manifest Metadata

**Files:**
- Modify: `custom_components/ha_weather_provider/manifest.json`
- Test: `tests/test_manifest.py`

- [ ] **Step 1: Write manifest metadata test**

Create `tests/test_manifest.py`:

```python
"""Tests for Home Assistant integration manifest metadata."""

from __future__ import annotations

import json
from pathlib import Path


MANIFEST_PATH = Path("custom_components/ha_weather_provider/manifest.json")


def test_manifest_declares_cloud_polling_service_metadata() -> None:
    """The integration manifest identifies this as a cloud polling service."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["iot_class"] == "cloud_polling"
    assert manifest["integration_type"] == "service"
    assert (
        manifest["issue_tracker"]
        == "https://git.kener.org/my-projects/ha-weather-provider/-/issues"
    )
    assert manifest["codeowners"] == ["@akener"]
```

- [ ] **Step 2: Run the failing manifest test**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_manifest.py -q`

Expected: FAIL with `KeyError: 'iot_class'`.

- [ ] **Step 3: Update manifest metadata**

Modify `custom_components/ha_weather_provider/manifest.json`:

```json
{
  "domain": "ha_weather_provider",
  "name": "HA Weather Provider",
  "version": "0.2.0",
  "config_flow": true,
  "documentation": "https://git.kener.org/my-projects/ha-weather-provider",
  "issue_tracker": "https://git.kener.org/my-projects/ha-weather-provider/-/issues",
  "requirements": [],
  "codeowners": ["@akener"],
  "iot_class": "cloud_polling",
  "integration_type": "service"
}
```

- [ ] **Step 4: Run manifest test**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_manifest.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha_weather_provider/manifest.json tests/test_manifest.py
git commit -m "Add HA manifest metadata"
```

### Task 2: Add Redacted Diagnostics

**Files:**
- Create: `custom_components/ha_weather_provider/diagnostics.py`
- Test: `tests/test_diagnostics.py`

- [ ] **Step 1: Write diagnostics tests**

Create `tests/test_diagnostics.py`:

```python
"""Tests for integration diagnostics."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_weather_provider.const import (
    CONF_DAILY_FORECAST_DURATION,
    CONF_ENABLE_AIR_QUALITY,
    CONF_ENABLE_POLLEN,
    CONF_ENABLE_TROPICAL_WEATHER,
    CONF_EXTRA_ENTITIES,
    CONF_HOURLY_FORECAST_DURATION,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_UNITS,
    CONF_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)
from custom_components.ha_weather_provider.coordinator import (
    TWCWeatherCoordinator,
    TWCWeatherData,
)
from custom_components.ha_weather_provider.diagnostics import (
    async_get_config_entry_diagnostics,
)


class _Client:
    """Minimal coordinator client for diagnostics tests."""


def _entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id="entry-id",
        data={
            "api_key": "secret-api-key",
            CONF_LATITUDE: 33.931,
            CONF_LONGITUDE: -84.4677,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={
            CONF_DAILY_FORECAST_DURATION: "7day",
            CONF_HOURLY_FORECAST_DURATION: "2day",
            CONF_UPDATE_INTERVAL_MINUTES: 30,
            CONF_EXTRA_ENTITIES: True,
            CONF_ENABLE_POLLEN: True,
            CONF_ENABLE_TROPICAL_WEATHER: True,
            CONF_ENABLE_AIR_QUALITY: True,
        },
    )


@pytest.mark.asyncio
async def test_diagnostics_redacts_api_key_and_reports_options(hass: Any) -> None:
    """Diagnostics expose useful config context without leaking credentials."""
    entry = _entry()
    coordinator = TWCWeatherCoordinator(
        hass,
        _Client(),
        pollen_enabled=True,
        tropical_enabled=True,
        air_quality_enabled=True,
        update_interval=timedelta(minutes=30),
    )
    coordinator.data = TWCWeatherData(
        current={"temperature": 71},
        daily_forecast={"validTimeUtc": [1760000000]},
        hourly_forecast={"validTimeUtc": [1760000000]},
        alert_headlines={"alerts": []},
        pollen_forecast={"pollenForecast12hour": {}},
        pollen_observation={},
        tropical_current_position={},
        air_quality={"globalairquality": {}},
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["data"]["api_key"] == "**REDACTED**"
    assert "secret-api-key" not in str(diagnostics)
    assert diagnostics["entry"]["options"][CONF_ENABLE_AIR_QUALITY] is True
    assert diagnostics["coordinator"]["update_interval_seconds"] == 1800.0
    assert diagnostics["payloads"] == {
        "current": True,
        "daily_forecast": True,
        "hourly_forecast": True,
        "alert_headlines": True,
        "pollen_forecast": True,
        "pollen_observation": False,
        "tropical_current_position": False,
        "air_quality": True,
    }
```

- [ ] **Step 2: Run the failing diagnostics test**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_diagnostics.py -q`

Expected: FAIL with `ModuleNotFoundError` or `ImportError` for `diagnostics`.

- [ ] **Step 3: Add diagnostics implementation**

Create `custom_components/ha_weather_provider/diagnostics.py`:

```python
"""Diagnostics support for HA Weather Provider."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, INTEGRATION_VERSION
from .coordinator import TWCWeatherCoordinator

TO_REDACT = {"api_key"}


def _payload_present(payload: dict[str, Any]) -> bool:
    """Return whether a coordinator payload contains data."""
    return bool(payload)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostics for a config entry."""
    coordinator: TWCWeatherCoordinator | None = hass.data.get(DOMAIN, {}).get(
        config_entry.entry_id
    )

    diagnostics: dict[str, Any] = {
        "integration_version": INTEGRATION_VERSION,
        "entry": {
            "entry_id": config_entry.entry_id,
            "data": async_redact_data(dict(config_entry.data), TO_REDACT),
            "options": dict(config_entry.options),
        },
        "coordinator": {
            "last_update_success": (
                coordinator.last_update_success if coordinator is not None else None
            ),
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator is not None and coordinator.update_interval is not None
                else None
            ),
            "pollen_enabled": (
                coordinator.pollen_enabled if coordinator is not None else None
            ),
            "tropical_enabled": (
                coordinator.tropical_enabled if coordinator is not None else None
            ),
            "air_quality_enabled": (
                coordinator.air_quality_enabled if coordinator is not None else None
            ),
        },
        "payloads": {},
    }

    if coordinator is not None and coordinator.data is not None:
        diagnostics["payloads"] = {
            "current": _payload_present(coordinator.data.current),
            "daily_forecast": _payload_present(coordinator.data.daily_forecast),
            "hourly_forecast": _payload_present(coordinator.data.hourly_forecast),
            "alert_headlines": _payload_present(coordinator.data.alert_headlines),
            "pollen_forecast": _payload_present(coordinator.data.pollen_forecast),
            "pollen_observation": _payload_present(
                coordinator.data.pollen_observation
            ),
            "tropical_current_position": _payload_present(
                coordinator.data.tropical_current_position
            ),
            "air_quality": _payload_present(coordinator.data.air_quality),
        }

    return diagnostics
```

- [ ] **Step 4: Run diagnostics tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_diagnostics.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha_weather_provider/diagnostics.py tests/test_diagnostics.py
git commit -m "Add redacted integration diagnostics"
```

### Task 3: Normalize Optional Endpoint Handling

**Files:**
- Modify: `twc_weather_client/client.py`
- Modify: `twc_weather_client/__init__.py`
- Modify: `custom_components/ha_weather_provider/coordinator.py`
- Test: `tests/test_twc_client.py`
- Test: `tests/test_coordinator.py`

- [ ] **Step 1: Write optional endpoint classification tests**

Append to `tests/test_twc_client.py`:

```python
from twc_weather_client import is_optional_endpoint_unavailable


def test_is_optional_endpoint_unavailable_identifies_no_data_and_entitlement() -> None:
    """Optional endpoint no-data and entitlement errors are non-fatal."""
    assert is_optional_endpoint_unavailable(TWCNoDataError("no data")) is True
    assert is_optional_endpoint_unavailable(TWCPermissionError("not entitled")) is True
    assert is_optional_endpoint_unavailable(TWCAuthError("bad key")) is True
    assert is_optional_endpoint_unavailable(TWCRequestError("server down")) is False
```

- [ ] **Step 2: Run the failing client test**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_twc_client.py::test_is_optional_endpoint_unavailable_identifies_no_data_and_entitlement -q`

Expected: FAIL with `ImportError` for `is_optional_endpoint_unavailable`.

- [ ] **Step 3: Add optional endpoint helper**

Add to `twc_weather_client/client.py`:

```python
def is_optional_endpoint_unavailable(error: Exception) -> bool:
    """Return whether an optional TWC endpoint failure should be non-fatal."""
    return isinstance(error, (TWCAuthError, TWCNoDataError, TWCPermissionError))
```

Export it from `twc_weather_client/__init__.py`:

```python
from .client import TWCClient, is_optional_endpoint_unavailable
```

Add `"is_optional_endpoint_unavailable"` to `__all__`.

- [ ] **Step 4: Use helper in coordinator optional fetches**

Modify `custom_components/ha_weather_provider/coordinator.py` imports:

```python
from twc_weather_client import (
    TWCAuthError,
    TWCClient,
    TWCError,
    TWCNoDataError,
    TWCPermissionError,
    is_optional_endpoint_unavailable,
)
```

Update optional endpoint exception handling to use the helper:

```python
            except TWCError as err:
                if is_optional_endpoint_unavailable(err):
                    _LOGGER.debug("Optional TWC pollen forecast endpoint is unavailable")
                else:
                    raise UpdateFailed(str(err)) from err
```

Use the same pattern for:

- Pollen forecast.
- Pollen observation.
- Tropical current position.
- Air quality.

Keep required current/daily/hourly/auth behavior unchanged.

- [ ] **Step 5: Run endpoint handling tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_twc_client.py tests/test_coordinator.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add twc_weather_client/client.py twc_weather_client/__init__.py custom_components/ha_weather_provider/coordinator.py tests/test_twc_client.py tests/test_coordinator.py
git commit -m "Normalize optional endpoint failures"
```

### Task 4: Document Polling and Optional Endpoint Behavior

**Files:**
- Create: `docs/operations.md`
- Modify: `docs/weather-card-gallery-dependencies.md`
- Test: `tests/test_docs.py`

- [ ] **Step 1: Write docs tests**

Create `tests/test_docs.py`:

```python
"""Tests for support and operations documentation."""

from __future__ import annotations

from pathlib import Path


OPERATIONS_DOC = Path("docs/operations.md")


def test_operations_doc_covers_polling_and_optional_endpoints() -> None:
    """Operations docs explain refresh behavior and endpoint fan-out."""
    text = OPERATIONS_DOC.read_text(encoding="utf-8")

    assert "Default refresh interval" in text
    assert "Required endpoints" in text
    assert "Optional endpoints" in text
    assert "API key entitlement" in text
    assert "/v3/wx/observations/current" in text
    assert "/v3/wx/forecast/daily" in text
    assert "/v3/wx/forecast/hourly" in text
    assert "/v3/alerts/headlines" in text
    assert "/v3/wx/globalAirQuality" in text
```

- [ ] **Step 2: Run the failing docs test**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_docs.py -q`

Expected: FAIL with `FileNotFoundError` for `docs/operations.md`.

- [ ] **Step 3: Add operations documentation**

Create `docs/operations.md`:

```markdown
# Operations

## Default refresh interval

The integration uses Home Assistant's `DataUpdateCoordinator` and polls The Weather Company APIs. The default refresh interval is 30 minutes. The options flow can change the interval within the supported range exposed by the integration.

## Required endpoints

Every refresh requests the core weather payloads:

- Current observations: `/v3/wx/observations/current`
- Daily forecast: `/v3/wx/forecast/daily/<duration>`
- Hourly forecast: `/v3/wx/forecast/hourly/<duration>`
- Alert headlines: `/v3/alerts/headlines`

The daily and hourly duration path segments come from integration options. The default daily duration is `7day`; the default hourly duration is `2day`.

## Optional endpoints

Optional endpoints are requested only when their options are enabled:

- Pollen forecast: `/v2/indices/pollen/daypart/<duration>`
- U.S. pollen observation: `/v1/geocode/<latitude>/<longitude>/observations/pollen.json`
- Tropical current position: `/v2/tropical/currentposition`
- Global air quality: `/v3/wx/globalAirQuality`

Optional endpoint failures caused by missing package access, no data, or unavailable data do not break the main `weather.twc` entity. The integration keeps core weather data available and exposes optional sensors only when data is available.

## API key entitlement

The Weather Company API keys can be entitled for different endpoint packages. A key can work for current conditions and forecasts while not being entitled for pollen, tropical weather, air quality, or other optional packages. When an optional package is not entitled, disable that option or leave the related entities unavailable.

## Polling model

The Weather Company Standard Weather Data package is polled over HTTPS. The integration does not use webhooks or MQTT because these endpoints are request/response APIs. Keep the refresh interval high enough to respect account quotas and avoid unnecessary Home Assistant updates.
```

- [ ] **Step 4: Link operations doc from gallery dependencies**

Append this sentence near the top of `docs/weather-card-gallery-dependencies.md`:

```markdown
Operational polling and endpoint entitlement behavior is documented in `docs/operations.md`.
```

- [ ] **Step 5: Run docs tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_docs.py tests/test_weather_card_gallery.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/operations.md docs/weather-card-gallery-dependencies.md tests/test_docs.py
git commit -m "Document polling and endpoint entitlements"
```

### Task 5: Add HACS and Local Development Metadata

**Files:**
- Create: `hacs.json`
- Create: `scripts/develop`
- Modify: `docs/operations.md`
- Test: `tests/test_repo_metadata.py`

- [ ] **Step 1: Write repository metadata tests**

Create `tests/test_repo_metadata.py`:

```python
"""Tests for custom integration repository metadata."""

from __future__ import annotations

import json
from pathlib import Path


HACS_PATH = Path("hacs.json")
DEVELOP_SCRIPT_PATH = Path("scripts/develop")


def test_hacs_metadata_declares_compatibility() -> None:
    """HACS metadata declares the integration name and compatibility floors."""
    hacs = json.loads(HACS_PATH.read_text(encoding="utf-8"))

    assert hacs["name"] == "The Weather Company"
    assert hacs["homeassistant"] >= "2026.3.2"
    assert hacs["hacs"] >= "2.0.5"


def test_develop_script_uses_custom_components_pythonpath() -> None:
    """Local HA development script exposes custom_components on PYTHONPATH."""
    text = DEVELOP_SCRIPT_PATH.read_text(encoding="utf-8")

    assert "PYTHONPATH" in text
    assert "custom_components" in text
    assert "hass --config" in text
```

- [ ] **Step 2: Run the failing metadata tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_repo_metadata.py -q`

Expected: FAIL with `FileNotFoundError` for `hacs.json` or `scripts/develop`.

- [ ] **Step 3: Add HACS metadata**

Create `hacs.json`:

```json
{
  "name": "The Weather Company",
  "homeassistant": "2026.3.2",
  "hacs": "2.0.5"
}
```

- [ ] **Step 4: Add local development script**

Create `scripts/develop`:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

CONFIG_DIR="${PWD}/config"
mkdir -p "${CONFIG_DIR}"

if [[ ! -f "${CONFIG_DIR}/configuration.yaml" ]]; then
  hass --config "${CONFIG_DIR}" --script ensure_config
fi

export PYTHONPATH="${PYTHONPATH:-}:${PWD}/custom_components"
hass --config "${CONFIG_DIR}" --debug
```

Make it executable:

```bash
chmod +x scripts/develop
```

- [ ] **Step 5: Document HACS and local development metadata**

Append to `docs/operations.md`:

```markdown
## Local development

The `scripts/develop` helper starts Home Assistant with `custom_components` on `PYTHONPATH`, matching the custom integration layout used by common blueprint repositories.

## HACS metadata

The repository includes `hacs.json` to declare the integration display name and minimum Home Assistant/HACS versions for future HACS distribution.
```

- [ ] **Step 6: Run metadata tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_repo_metadata.py tests/test_docs.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add hacs.json scripts/develop docs/operations.md tests/test_repo_metadata.py
git commit -m "Add HACS and development metadata"
```

### Task 6: Remove Tracked Generated Files

**Files:**
- Modify: `.gitignore`
- Remove: tracked generated cache files discovered by `git ls-files`
- Test: no pytest test; use git commands

- [ ] **Step 1: Check tracked cache files**

Run: `git ls-files '*__pycache__*' '.pytest_cache/*' '.ruff_cache/*'`

Expected if cache files are tracked: output includes generated files such as `custom_components/ha_weather_provider/__pycache__/...` or `tests/__pycache__/...`.

Expected if no cache files are tracked: no output.

- [ ] **Step 2: Ensure ignore rules exist**

Open `.gitignore`. It must contain:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/
.venv/
venv/
.env
```

If any entry is missing, add it.

- [ ] **Step 3: Remove tracked generated files**

If Step 1 printed tracked generated files, remove them from git:

```bash
git rm -r --cached custom_components/ha_weather_provider/__pycache__ tests/__pycache__ .pytest_cache .ruff_cache
```

If a listed path does not exist, rerun `git ls-files '*__pycache__*' '.pytest_cache/*' '.ruff_cache/*'` and pass the exact tracked paths to `git rm --cached`.

- [ ] **Step 4: Verify generated files are untracked or ignored**

Run: `git status --short --ignored | rg "__pycache__|pytest_cache|ruff_cache" || true`

Expected: generated files appear only as ignored entries with `!!`, or no output if the files are absent.

- [ ] **Step 5: Commit hygiene changes**

If `.gitignore` or tracked generated files changed:

```bash
git add .gitignore
git add -u
git commit -m "Remove generated cache files from repository"
```

If nothing changed, do not create an empty commit.

### Task 7: Final Verification

**Files:**
- Modify: no files unless verification exposes a defect

- [ ] **Step 1: Run targeted tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_manifest.py tests/test_diagnostics.py tests/test_twc_client.py tests/test_coordinator.py tests/test_docs.py tests/test_repo_metadata.py -q`

Expected: PASS.

- [ ] **Step 2: Run Ruff**

Run: `.worktrees/demo-dashboard-card/.venv/bin/ruff check twc_weather_client custom_components/ha_weather_provider tests`

Expected: PASS.

- [ ] **Step 3: Run full project checks**

Run: `PATH=".worktrees/demo-dashboard-card/.venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .`

Expected: compile, JSON validation, Ruff/harness checks, and pytest all pass.

- [ ] **Step 4: Commit verification fixes**

If verification required fixes:

```bash
git add twc_weather_client custom_components/ha_weather_provider docs tests .gitignore
git commit -m "Stabilize HA integration hardening"
```

If no fixes were needed, do not create an empty commit.

- [ ] **Step 5: Push branch**

```bash
git push origin ha-integration-hardening
```

Expected: branch is pushed and ready for a GitLab MR into `master`.
