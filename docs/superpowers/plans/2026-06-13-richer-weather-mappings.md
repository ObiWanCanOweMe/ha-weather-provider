# Richer Weather Mappings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich the existing The Weather Company Home Assistant `weather` entity with additional current-condition and daily-forecast fields that Home Assistant natively supports.

**Architecture:** Keep this milestone scoped to the one weather entity. Map only fields that are present in the TWC current and 7-day daily forecast payloads and already supported by Home Assistant weather properties. Do not add separate sensor entities in this milestone.

**Tech Stack:** Home Assistant custom integration, TWC Weather Data API, pytest, obi-dev-harness.

---

### Task 1: Current Condition Fields

**Files:**
- Modify: `custom_components/ha_weather_provider/weather.py`
- Test: `tests/test_weather.py`

- [x] Add failing assertions for current dew point and cloud cover.
- [x] Map `native_dew_point` from TWC `temperatureDewPoint`.
- [x] Map `cloud_coverage` from TWC `cloudCover`.
- [x] Run `pytest tests/test_weather.py -q`.

### Task 2: Daily Forecast Fields

**Files:**
- Modify: `custom_components/ha_weather_provider/weather.py`
- Test: `tests/test_weather.py`

- [x] Add failing assertions for daily forecast humidity, apparent temperature, cloud cover, precipitation amount, and UV index.
- [x] Map daytime `relativeHumidity`, `cloudCover`, `qpf`, and `uvIndex` from the interlaced daypart arrays.
- [x] Map daytime apparent temperature from `temperatureHeatIndex`, falling back to `temperatureWindChill`.
- [x] Preserve existing malformed-payload behavior by omitting unavailable values.
- [x] Run `pytest tests/test_weather.py -q`.

### Task 3: Verification and Merge Request

**Files:**
- Modify: branch metadata only as needed.

- [x] Run the full test suite.
- [x] Run `obi-dev-harness project-check .`.
- [x] Restart the Home Assistant test container mounted to this worktree and check integration startup logs.
- [x] Commit and push `richer-weather-mappings`.
- [x] Open a GitLab MR into `master` assigned to the `Richer Current and Daily Weather Mappings` milestone.
