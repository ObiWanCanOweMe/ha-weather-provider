# Options Flow Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe update interval option to the Home Assistant options flow while keeping the default setup simple.

**Architecture:** Extend the existing options flow with an `update_interval_minutes` selector using conservative fixed choices. Pass the selected interval into `TWCWeatherCoordinator` during setup, falling back to the existing 30-minute default for existing entries or malformed options. Keep forecast length out of this slice.

**Tech Stack:** Home Assistant config entries/options flow, `DataUpdateCoordinator`, pytest, ruff.

---

### Task 1: Options Flow Test Coverage

**Files:**
- Modify: `tests/test_config_flow.py`
- Modify: `custom_components/ha_weather_provider/config_flow.py`
- Modify: `custom_components/ha_weather_provider/const.py`
- Modify: `custom_components/ha_weather_provider/strings.json`
- Modify: `custom_components/ha_weather_provider/translations/en.json`

- [x] **Step 1: Write failing options-flow test**

Add assertions that options can save both `extra_entities` and `update_interval_minutes`.

- [x] **Step 2: Run focused test to verify failure**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_config_flow.py::test_options_flow_configures_update_interval_controls -q`

Expected: FAIL because `CONF_UPDATE_INTERVAL_MINUTES` is not defined.

- [x] **Step 3: Add constants and options schema**

Add `CONF_UPDATE_INTERVAL_MINUTES`, `DEFAULT_UPDATE_INTERVAL_MINUTES`, and `UPDATE_INTERVAL_MINUTES`. Include the new option in `HAWeatherProviderOptionsFlow`.

- [x] **Step 4: Verify options-flow test passes**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_config_flow.py::test_options_flow_configures_update_interval_controls -q`

Expected: PASS.

### Task 2: Coordinator Interval Wiring

**Files:**
- Modify: `tests/test_init.py`
- Modify: `tests/test_coordinator.py`
- Modify: `custom_components/ha_weather_provider/__init__.py`
- Modify: `custom_components/ha_weather_provider/coordinator.py`

- [x] **Step 1: Write failing setup/coordinator tests**

Add tests that a config entry option of `60` minutes is passed into the coordinator and that the coordinator stores an explicitly provided interval.

- [x] **Step 2: Run focused tests to verify failure**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_init.py::test_async_setup_entry_uses_configured_update_interval tests/test_coordinator.py::test_coordinator_uses_configured_update_interval -q`

Expected: FAIL because the coordinator constructor does not accept a custom update interval.

- [x] **Step 3: Implement update interval plumbing**

Allow `TWCWeatherCoordinator` to accept `update_interval`, and have setup derive it from config entry options with a default fallback.

- [x] **Step 4: Verify focused tests pass**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_init.py::test_async_setup_entry_uses_configured_update_interval tests/test_coordinator.py::test_coordinator_uses_configured_update_interval -q`

Expected: PASS.

### Task 3: Verification and MR

**Files:**
- Test: all files

- [x] **Step 1: Run full test suite**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest`

Expected: PASS.

- [x] **Step 2: Run lint**

Run: `../demo-dashboard-card/.venv/bin/ruff check .`

Expected: PASS.

- [x] **Step 3: Run harness checks**

Run: `PATH="../demo-dashboard-card/.venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .`

Expected: PASS.
