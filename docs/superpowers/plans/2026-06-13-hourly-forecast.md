# Hourly Forecast Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add The Weather Company 2-day hourly forecast support to the Home Assistant weather entity.

**Architecture:** Extend the existing current/daily pattern with a third API call to `/v3/wx/forecast/hourly/2day`, store it in `TWCWeatherData`, and expose it through `WeatherEntityFeature.FORECAST_HOURLY` plus `async_forecast_hourly()`. Keep setup validation strict enough that the first refresh proves hourly entitlement is available.

**Tech Stack:** Home Assistant custom integration, aiohttp, TWC Weather Data API, pytest, aioresponses.

---

### Task 1: API Client Endpoint

**Files:**
- Modify: `custom_components/ha_weather_provider/api.py`
- Test: `tests/test_api.py`

- [ ] Add a failing test that `async_get_hourly_forecast()` calls `/v3/wx/forecast/hourly/2day`.
- [ ] Add `HOURLY_FORECAST_PATH = "/v3/wx/forecast/hourly/2day"` and `async_get_hourly_forecast()`.
- [ ] Run `pytest tests/test_api.py -q`.

### Task 2: Coordinator Payload

**Files:**
- Modify: `custom_components/ha_weather_provider/coordinator.py`
- Test: `tests/test_coordinator.py`

- [ ] Add a failing test that coordinator data includes `hourly_forecast`.
- [ ] Add `hourly_forecast` to `TWCWeatherData` and fetch it in `_async_update_data()`.
- [ ] Run `pytest tests/test_coordinator.py -q`.

### Task 3: Weather Entity Hourly Mapping

**Files:**
- Modify: `custom_components/ha_weather_provider/weather.py`
- Test: `tests/test_weather.py`

- [ ] Add failing tests for `FORECAST_HOURLY` and `async_forecast_hourly()`.
- [ ] Map hourly arrays by index from `validTimeUtc`, `iconCode`, `wxPhraseLong`, `temperature`, `temperatureFeelsLike`, `precipChance`, `qpf`, `windSpeed`, `windGust`, `windDirection`, `relativeHumidity`, `pressureMeanSeaLevel`, and `uvIndex`.
- [ ] Skip malformed timestamps and omit `None` values, matching daily forecast behavior.
- [ ] Run `pytest tests/test_weather.py -q`.

### Task 4: Verification and Integration Handoff

**Files:**
- Modify: only generated branch metadata as needed.

- [ ] Run `obi-dev-harness project-check .`.
- [ ] Restart the HA test container mounted to the hourly worktree for runtime testing.
- [ ] Commit and push `hourly-forecast`.
- [ ] Open a GitLab MR into `master` assigned to the `Hourly Forecast` milestone.
