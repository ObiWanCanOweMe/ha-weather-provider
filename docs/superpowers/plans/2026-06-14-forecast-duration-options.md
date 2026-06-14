# Forecast Duration Options Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users choose documented The Weather Company daily and hourly forecast durations from the integration options flow.

**Architecture:** Keep forecast duration as config-entry options with conservative defaults that preserve current behavior. The API client owns path construction, while setup reads and validates option values before constructing the client.

**Tech Stack:** Home Assistant custom integration, Python, aiohttp, voluptuous, pytest, aioresponses.

---

### Task 1: API Client Forecast Duration Paths

**Files:**
- Modify: `custom_components/ha_weather_provider/const.py`
- Modify: `custom_components/ha_weather_provider/api.py`
- Test: `tests/test_api.py`

- [x] **Step 1: Write failing API tests**

Add tests that instantiate `TWCClient` with `daily_forecast_duration="15day"` and `hourly_forecast_duration="6hour"` and assert those exact endpoint paths are requested.

- [x] **Step 2: Run focused tests and verify failure**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_api.py -q`

Expected: failure because `TWCClient` does not accept forecast duration arguments yet.

- [x] **Step 3: Implement client duration support**

Add duration constants to `const.py`, import defaults into `api.py`, and have `TWCClient` build daily/hourly paths from the configured duration.

- [x] **Step 4: Run focused tests and verify pass**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_api.py -q`

Expected: all API tests pass.

### Task 2: Options Flow and Setup Wiring

**Files:**
- Modify: `custom_components/ha_weather_provider/config_flow.py`
- Modify: `custom_components/ha_weather_provider/__init__.py`
- Modify: `custom_components/ha_weather_provider/strings.json`
- Modify: `custom_components/ha_weather_provider/translations/en.json`
- Test: `tests/test_config_flow.py`
- Test: `tests/test_init.py`

- [x] **Step 1: Write failing options/setup tests**

Add tests that the options flow stores both forecast duration options and setup passes selected values into `TWCClient`. Add one setup fallback test for invalid stored option values.

- [x] **Step 2: Run focused tests and verify failure**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_config_flow.py tests/test_init.py -q`

Expected: failures because duration constants, schema fields, and setup kwargs do not exist yet.

- [x] **Step 3: Implement options and setup wiring**

Expose `daily_forecast_duration` and `hourly_forecast_duration` in the options schema, preserve existing defaults, and pass sanitized values into `TWCClient` from setup.

- [x] **Step 4: Run focused tests and verify pass**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_config_flow.py tests/test_init.py -q`

Expected: config flow and setup tests pass.

### Task 3: Full Verification and MR

**Files:**
- Modify: `docs/superpowers/plans/2026-06-14-forecast-duration-options.md`

- [x] **Step 1: Run full tests**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest`

Expected: all tests pass.

- [x] **Step 2: Run lint**

Run: `../demo-dashboard-card/.venv/bin/ruff check .`

Expected: no lint failures.

- [x] **Step 3: Run project checks**

Run: `PATH="../demo-dashboard-card/.venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .`

Expected: all recommended checks pass.

- [x] **Step 4: Commit, push, and open MR**

Commit the plan and implementation, push `forecast-duration-options`, and open a GitLab MR into `master` assigned to the `Options Flow and Entity Controls` milestone.
