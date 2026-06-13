# Optional Extra Entities Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional first slice of companion diagnostic sensors while keeping the main `weather.twc` entity as the default experience.

**Architecture:** Always forward the `sensor` platform, but create no sensor entities unless the config entry option `extra_entities` is enabled. Sensor entities read from the existing `TWCWeatherCoordinator` cache and do not make additional API calls. The demo card keeps weather data accurate by showing `No gust reported` when the Weather Company current observation omits gust data.

**Tech Stack:** Home Assistant config entries/options flow, `SensorEntity`, existing TWC coordinator, pytest, Lovelace YAML.

---

### Task 1: Demo Wind Gust Copy

**Files:**
- Modify: `dashboards/the-weather-company-demo.yaml`
- Modify: `tests/test_dashboard_demo.py`

- [x] **Step 1: Write failing dashboard test**

Add `test_demo_dashboard_explains_missing_wind_gust` to assert the card contains `No gust reported` and no longer renders missing gusts as `Unavailable`.

- [x] **Step 2: Run the focused dashboard test**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_dashboard_demo.py::test_demo_dashboard_explains_missing_wind_gust -q`

Expected: FAIL because the dashboard still says `Unavailable`.

- [x] **Step 3: Update dashboard YAML**

Change the wind gust row to:

```yaml
| Wind gust | {{ wind_gust ~ ' ' ~ wind_speed_unit if wind_gust is not none else 'No gust reported' }} |
```

- [x] **Step 4: Verify focused dashboard test**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_dashboard_demo.py -q`

Expected: PASS.

### Task 2: Options Flow

**Files:**
- Modify: `custom_components/ha_weather_provider/config_flow.py`
- Modify: `custom_components/ha_weather_provider/const.py`
- Modify: `custom_components/ha_weather_provider/strings.json`
- Modify: `custom_components/ha_weather_provider/translations/en.json`
- Modify: `tests/test_config_flow.py`

- [x] **Step 1: Write failing options-flow test**

Add `test_options_flow_configures_optional_extra_entities` to assert the config entry options flow can set `{CONF_EXTRA_ENTITIES: True}`.

- [x] **Step 2: Run the focused options-flow test**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_config_flow.py::test_options_flow_configures_optional_extra_entities -q`

Expected: FAIL because `CONF_EXTRA_ENTITIES` and the options flow do not exist.

- [x] **Step 3: Implement options flow**

Add `CONF_EXTRA_ENTITIES = "extra_entities"` and return an `OptionsFlowWithReload` from the config flow. The options schema uses a boolean toggle with a default of `False`.

- [x] **Step 4: Add option strings**

Add `options.step.init` strings for the Home Assistant options dialog.

### Task 3: Optional Sensor Platform

**Files:**
- Create: `custom_components/ha_weather_provider/sensor.py`
- Modify: `custom_components/ha_weather_provider/__init__.py`
- Create: `tests/test_sensor.py`

- [x] **Step 1: Write failing sensor tests**

Add tests proving sensors are skipped by default, created when `extra_entities` is enabled, and map values from coordinator data.

- [x] **Step 2: Run the focused sensor tests**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_sensor.py -q`

Expected: FAIL because there is no sensor platform.

- [x] **Step 3: Implement sensor platform**

Create five optional sensors:

- `alert_count`
- `condition_phrase`
- `observation_time`
- `integration_version`
- `wind_gust`

All sensors read from `TWCWeatherCoordinator.data`.

- [x] **Step 4: Verify focused sensor tests**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest tests/test_sensor.py -q`

Expected: PASS.

### Task 4: Verification

**Files:**
- Test: all project files

- [x] **Step 1: Run full pytest suite**

Run: `PYTHONPATH=. ../demo-dashboard-card/.venv/bin/pytest`

Expected: PASS.

- [x] **Step 2: Run lint**

Run: `../demo-dashboard-card/.venv/bin/ruff check .`

Expected: PASS.

- [x] **Step 3: Run harness checks**

Run: `PATH="../demo-dashboard-card/.venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .`

Expected: PASS.
