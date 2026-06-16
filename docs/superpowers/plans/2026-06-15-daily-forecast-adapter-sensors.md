# Daily Forecast Adapter Sensors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional daily forecast adapter sensors for five days and wire the Animated Weather Card to those sensors.

**Architecture:** Extend `custom_components/ha_weather_provider/sensor.py` with generated optional sensor descriptions for day 1-5 condition, high, low, precipitation probability, precipitation amount, and summary. Reuse the same TWC daily forecast helper semantics as the weather entity so adapter sensors and `weather.twc` agree. Update the gallery YAML to reference the dedicated forecast sensors and document the SVG asset path.

**Tech Stack:** Home Assistant custom integration sensors, pytest, PyYAML dashboard tests, Lovelace YAML.

---

### Task 1: Add Failing Sensor Tests

**Files:**
- Modify: `tests/test_sensor.py`

- [ ] **Step 1: Write failing tests**

Add assertions that optional setup creates 30 daily forecast adapter sensors after the existing compact sensors, and that day 1/day 2 values map from TWC daily forecast fields.

- [ ] **Step 2: Run failing tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_sensor.py -q`

Expected: fail because the new sensor descriptions and mapper functions do not exist.

### Task 2: Implement Daily Forecast Sensor Descriptions

**Files:**
- Modify: `custom_components/ha_weather_provider/sensor.py`

- [ ] **Step 1: Add daily forecast mapping helpers**

Add local helpers for series values, daypart offsets, condition mapping, forecast high fallback, and safe string summaries.

- [ ] **Step 2: Generate five-day sensor descriptions**

Add descriptions with keys like `daily_forecast_day_1_condition`, names like `Daily Forecast Day 1 Condition`, and units for high/low/precip amount/probability.

- [ ] **Step 3: Run sensor tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_sensor.py -q`

Expected: pass.

### Task 3: Wire Gallery To Dedicated Forecast Sensors

**Files:**
- Modify: `dashboards/the-weather-company-card-gallery.yaml`
- Modify: `tests/test_weather_card_gallery.py`
- Modify: `docs/weather-card-gallery-dependencies.md`

- [ ] **Step 1: Update gallery tests first**

Expect Animated Weather Card forecast fields to reference `sensor.twc_daily_forecast_day_N_*` entities for condition, high, low, precipitation probability, precipitation amount, and summary.

- [ ] **Step 2: Update Lovelace YAML**

Replace repeated `sensor.twc_demo_*` forecast placeholders with dedicated daily forecast adapter entities and enable precipitation rows.

- [ ] **Step 3: Update docs**

Document the daily forecast adapter sensors and the already-installed `/config/www/icons/weather_icons/{animated,static}` SVG asset path.

- [ ] **Step 4: Run gallery tests**

Run: `PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_weather_card_gallery.py -q`

Expected: pass.

### Task 4: Apply And Verify In HA

**Files:**
- Live HA storage: `/Users/akener/.ha-weather-provider-test/config/.storage/lovelace.twc-card-gallery`
- Live HA custom component: `/Users/akener/.ha-weather-provider-test/config/custom_components/ha_weather_provider`

- [ ] **Step 1: Copy updated integration and dashboard into the test instance**

Use the existing local config paths and back up dashboard storage before replacing the view.

- [ ] **Step 2: Restart HA**

Run: `docker restart ha-weather-provider-test`

- [ ] **Step 3: Verify route, resources, and logs**

Check `/twc-card-gallery`, representative weather icons, and recent HA logs.

- [ ] **Step 4: Run full project checks**

Run: `PATH=".worktrees/demo-dashboard-card/.venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .`

Expected: pass.
