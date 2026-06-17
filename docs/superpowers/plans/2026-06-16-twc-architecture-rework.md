# TWC Architecture Rework Sprint Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development for each sprint, or superpowers:executing-plans for focused implementation tasks. Keep each sprint independently shippable and avoid changing public entity IDs unless the sprint explicitly calls for migration work.

**Goal:** Rework the integration so `weather.twc` is the primary user-facing surface, optional companion sensors are controlled and low-noise, endpoint refreshes are isolated by data family, and the Home Assistant integration layer follows the patterns used by core weather integrations such as AccuWeather.

**Architecture:** Move from one broad coordinator that fetches every enabled endpoint to endpoint-family coordinators feeding a `CoordinatorWeatherEntity`. Keep the current TWC client package boundary. Preserve existing entity IDs where practical, but reduce default entity creation and make high-cardinality or demo-card-oriented entities opt-in or disabled by default.

**Tech Stack:** Home Assistant custom integration APIs, `CoordinatorWeatherEntity`, `DataUpdateCoordinator`, config/options flow, entity registry defaults, diagnostics, pytest, pytest-homeassistant-custom-component, ruff, obi-dev-harness.

---

## Reference Model

Use Home Assistant core AccuWeather as the primary comparison point:

- It registers only `sensor` and `weather` platforms.
- It does not register custom integration services.
- Generic HA weather forecast services are backed by the weather entity forecast methods.
- It uses separate coordinators for observation, daily forecast, and hourly forecast.
- It uses `CoordinatorWeatherEntity`.
- It sets `DeviceInfo` with `DeviceEntryType.SERVICE`.
- It uses `_attr_has_entity_name = True`, translation keys, and stable unique IDs.
- It creates forecast sensors only when the forecast payload contains the required key.
- It marks many non-essential sensors as `entity_registry_enabled_default=False`.

Current TWC gaps:

- One broad coordinator fetches current, daily, hourly, alerts, pollen, tropical, and air quality together.
- Optional endpoint failures can affect broader refresh behavior.
- Optional sensor groups can produce about 198 entities when enabled.
- Sensor descriptions are coarse-option controlled but not disabled by default after creation.
- Entity/device naming is less aligned with core HA patterns.
- We do not yet provide `system_health.py` or `icons.json`.

## Non-Goals

- Do not remove `weather.twc`.
- Do not remove existing optional data families such as pollen, air quality, or tropical summary.
- Do not add custom services unless a real use case remains after the weather entity and forecast APIs are cleaned up.
- Do not bundle third-party dashboard cards into the integration in this architecture pass.
- Do not change TWC API payload semantics in the client package unless needed to support coordinator boundaries.

## Release Strategy

Implement this as a series of small merge requests. Each sprint should leave the integration usable in the HA test instance and should pass the full project check before merge.

Recommended branch sequence:

1. `rearchitecture-coordinators`
2. `rearchitecture-weather-entity`
3. `rearchitecture-entity-surface`
4. `rearchitecture-platform-polish`
5. `rearchitecture-docs-and-migration`

The current branch `rearchitecture-weather-services` can remain the analysis branch or become the first implementation branch.

---

## Sprint 0: Baseline Inventory and Safety Net

**Objective:** Capture current behavior before changing architecture.

**Scope:**

- Add or update tests that count entity creation by options.
- Document current default, extra, pollen, air quality, and tropical entity counts.
- Assert `weather.twc` remains the primary entity.
- Assert current weather attributes and daily/hourly forecasts still expose the fields we care about.
- Add fixtures for enabled and disabled optional endpoint payloads.

**Implementation Tasks:**

- Add tests around `async_setup_entry` for the weather platform.
- Add tests around sensor platform entity counts by option set.
- Add a regression test for the install/options flow defaults.
- Add a short architecture inventory section to `docs/testing.md` or a new `docs/architecture.md`.

**Acceptance Criteria:**

- Tests clearly show the current entity count with all optional groups enabled.
- The test suite would fail if `weather.twc` disappears.
- The test suite would fail if current, daily forecast, or hourly forecast data is no longer available from the weather entity.

**Checks:**

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_weather.py tests/test_sensor.py tests/test_config_flow.py -q
.venv/bin/ruff check custom_components/ha_weather_provider tests
PATH=".venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .
```

**Merge Point:** Safe to merge when no runtime behavior has changed except added tests/docs.

---

## Sprint 1: Coordinator Separation

**Objective:** Split data refresh by endpoint family so core weather updates are not coupled to optional endpoints.

**Scope:**

- Introduce typed runtime data containing multiple coordinators.
- Split current observation, daily forecast, hourly forecast, alerts, pollen, air quality, and tropical into separate coordinator classes or a shared base coordinator with endpoint-specific subclasses.
- Preserve existing TWC client methods.
- Preserve existing update interval options initially, even if all core coordinators use the same selected interval.
- Optional endpoint unavailability should only affect that optional coordinator.

**Recommended Coordinator Model:**

- `TWCObservationCoordinator`
- `TWCDailyForecastCoordinator`
- `TWCHourlyForecastCoordinator`
- `TWCAlertCoordinator`
- `TWCPollenForecastCoordinator`
- `TWCPollenObservationCoordinator`
- `TWCTropicalCoordinator`
- `TWCAirQualityCoordinator`

**Implementation Tasks:**

- Replace `TWCWeatherData` as the main runtime object with a `TWCIntegrationData` dataclass that holds coordinators.
- Keep a compatibility layer temporarily if needed for existing sensor value functions.
- Run first refreshes with `asyncio.gather`, but only include optional coordinators when their option is enabled.
- Convert optional endpoint permission/no-data responses into coordinator-local empty payloads when appropriate.
- Update diagnostics to report per-coordinator last update success and payload availability.

**Acceptance Criteria:**

- Current, daily, hourly, and alerts refresh independently.
- Pollen failure does not make `weather.twc` unavailable.
- Air quality failure does not make `weather.twc` unavailable.
- Tropical failure does not make `weather.twc` unavailable.
- Existing tests continue to pass or are updated to target the new coordinator shape.

**Checks:**

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_coordinator.py tests/test_init.py tests/test_diagnostics.py -q
PATH=".venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .
```

**Merge Point:** Safe to merge when the runtime coordinator model is split but entity names and options remain stable.

---

## Sprint 2: Weather Entity Alignment

**Objective:** Make `weather.twc` follow the core weather integration pattern more closely.

**Scope:**

- Move weather entity to `CoordinatorWeatherEntity`.
- Feed it observation, daily, and hourly coordinators.
- Preserve `weather.twc` entity ID and unique ID behavior unless a migration is explicitly implemented.
- Keep all current weather properties and forecast dictionaries.
- Ensure generic HA weather forecast services continue to work through the entity.

**Implementation Tasks:**

- Refactor `HAWeatherProviderEntity` to inherit from `CoordinatorWeatherEntity`.
- Set `_attr_has_entity_name = True` and `_attr_name = None` if compatible with preserving `weather.twc`.
- Add `DeviceInfo` for The Weather Company service entry.
- Keep `integration_version`, `alert_count`, and `alert_headlines` as weather entity attributes or move them to companion sensors only after a deliberate decision.
- Update tests for daily and hourly forecasts to use the new coordinator shape.

**Acceptance Criteria:**

- `weather.twc` remains the default weather entity for new installs.
- Current attributes still include temperature, feels-like, humidity, pressure, wind speed, wind gust, wind bearing, visibility, UV index, dew point, and cloud coverage when TWC provides values.
- Daily forecasts still include high, low, apparent temperature, humidity, dew point, cloud coverage, precipitation probability, precipitation amount, wind speed, wind bearing, UV index, and condition when available.
- Hourly forecasts still include temperature, apparent temperature, humidity, pressure, cloud coverage, precipitation probability, precipitation amount, wind speed, wind gust, wind bearing, UV index, and condition when available.
- HA weather forecast services work through the weather entity.

**Checks:**

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_weather.py tests/test_dashboard_demo.py tests/test_weather_card_gallery.py -q
PATH=".venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .
```

**Merge Point:** Safe to merge when `weather.twc` is still stable and forecast services work.

---

## Sprint 3: Entity Surface Reduction

**Objective:** Reduce entity noise while keeping useful companion sensors available.

**Scope:**

- Reclassify optional sensors into default-enabled and disabled-by-default groups.
- Keep critical compact sensors available when the matching option is enabled.
- Disable demo-card adapter and high-cardinality forecast sensors by default.
- Create forecast sensors only when the source payload contains the relevant field.

**Recommended Entity Policy:**

- Always enabled by default:
  - `weather.twc`
- Enabled by default when "current detail sensors" are enabled:
  - temperature
  - feels-like
  - dew point
  - humidity
  - pressure
  - cloud cover
  - UV index
  - visibility
  - wind speed
  - wind bearing
  - condition phrase/code
  - observation time
- Disabled by default even when created:
  - wind gust, if often missing locally
  - precipitation rate/intensity, unless confirmed by endpoint
  - all per-day adapter sensors
  - all demo-card compatibility sensors
  - any sensor that duplicates a weather entity attribute without strong automation value
- Separate optional groups:
  - current detail sensors
  - forecast adapter sensors
  - pollen sensors
  - air quality sensors
  - tropical summary sensors

**Implementation Tasks:**

- Add `entity_registry_enabled_default=False` to non-essential `TWCSensorEntityDescription` entries.
- Consider adding a field to `TWCSensorEntityDescription` for `requires_payload_key` or `availability_fn`.
- Make per-day forecast sensor creation data-driven, similar to AccuWeather.
- Split the current `extra_entities` option into smaller options, with migration from the old option:
  - old `extra_entities=True` should enable current details and forecast adapters for existing users.
  - new installs should show clearer grouped options.
- Update strings and translations for the new option groups.

**Acceptance Criteria:**

- A default new install creates only `weather.twc`.
- Enabling current detail sensors creates a modest, predictable set.
- Enabling all optional groups no longer enables every high-cardinality/demo sensor by default.
- Existing users with `extra_entities=True` are not silently stripped of entities without a migration note or compatibility behavior.
- Missing TWC values result in unavailable/unknown states only for the specific affected sensor, not broad groups.

**Checks:**

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_sensor.py tests/test_config_flow.py tests/test_init.py -q
PATH=".venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .
```

**Merge Point:** This sprint changes user-visible entity creation. Merge only after testing in a fresh HA instance and an upgraded HA instance.

---

## Sprint 4: Config, Migration, and Registry Cleanup

**Objective:** Make the new architecture safe for existing installs.

**Scope:**

- Add config entry migration if options are renamed or split.
- Preserve stable unique IDs where possible.
- Add targeted registry cleanup only for entities we intentionally retire.
- Avoid deleting user-customized entities unless absolutely necessary.

**Implementation Tasks:**

- Add `async_migrate_entry` for option shape changes.
- Map old `extra_entities` to new grouped options.
- Add tests for old config entry versions and old options.
- If any old unique IDs are retired, add a conservative cleanup path and tests.
- Document upgrade behavior in README and `docs/operations.md`.

**Acceptance Criteria:**

- Existing installs continue to load.
- Existing `weather.twc` remains stable.
- Old options migrate to new options.
- Registry cleanup is narrow and documented.
- Fresh install and upgrade install both pass manual HA smoke testing.

**Checks:**

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_init.py tests/test_config_flow.py tests/test_sensor.py -q
PATH=".venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .
```

**Merge Point:** Merge after fresh and upgraded HA test instance verification.

---

## Sprint 5: Platform Polish

**Objective:** Bring integration metadata and Home Assistant polish closer to core examples.

**Scope:**

- Add `system_health.py`.
- Add `icons.json`.
- Improve device metadata.
- Improve translated entity names.
- Improve coordinator error messages with translation keys where practical.

**Implementation Tasks:**

- Add `DeviceInfo` helper with:
  - `entry_type=DeviceEntryType.SERVICE`
  - identifiers based on domain and stable location/config unique ID
  - manufacturer "The Weather Company"
  - configuration URL if a useful TWC URL exists, otherwise omit
- Add `system_health.py` reporting configured optional endpoint groups and last update status without exposing API keys.
- Add `icons.json` for common sensors.
- Replace hand-built sensor display names with translation keys where practical.
- Confirm HACS packaging still works.

**Acceptance Criteria:**

- Device page groups weather and sensors under a service device.
- System health exposes useful, redacted integration status.
- Entity names follow HA conventions.
- Icons are present for common sensors.
- No credentials appear in diagnostics or system health.

**Checks:**

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_diagnostics.py tests/test_manifest.py tests/test_sensor.py -q
PATH=".venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .
```

**Merge Point:** Safe to merge after UI smoke testing in HA settings, device page, entity list, and diagnostics.

---

## Sprint 6: Dashboard and Demo Compatibility

**Objective:** Keep demo dashboards useful after the entity surface reduction.

**Scope:**

- Update the TWC demo dashboard to prefer weather entity data where possible.
- Keep adapter sensors only where third-party cards require individual entities.
- Mark missing optional dependencies clearly in docs.

**Implementation Tasks:**

- Review `docs/weather-card-gallery.md` and dashboard YAML against the new entity groups.
- Update dashboard cards to use `weather.twc` directly where supported.
- Update adapter sensor references for any renamed or disabled-by-default sensors.
- Update `docs/weather-card-gallery-dependencies.md`.
- Add tests that parse the dashboard YAML and assert referenced entities either exist by default or are documented as optional.

**Acceptance Criteria:**

- Demo dashboard still renders with `weather.twc` and documented optional sensors.
- Third-party card dependencies remain documented.
- The dashboard no longer drives core integration architecture by itself.

**Checks:**

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_dashboard_demo.py tests/test_weather_card_gallery.py -q
PATH=".venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .
```

**Merge Point:** Merge after visual review in the HA test instance.

---

## Sprint 7: Documentation, Release Notes, and HACS Validation

**Objective:** Make the architecture change understandable and installable.

**Scope:**

- Update README install/configuration docs.
- Add upgrade notes.
- Confirm GitLab to GitHub mirror and HACS install path.
- Update version if the change is released.

**Implementation Tasks:**

- Document default entity behavior.
- Document optional entity groups.
- Document why many sensors are disabled by default.
- Document how to enable disabled entities from HA Settings.
- Add a migration note for existing users with many entities.
- Run a fresh HA install through HACS from the GitHub mirror.
- Run an upgrade install from a previous version in the test HA instance.

**Acceptance Criteria:**

- README explains automatic and manual install paths.
- README explains default versus optional entities.
- HACS install works from `https://github.com/ObiWanCanOweMe/ha-weather-provider`.
- Fresh install creates the expected default entities.
- Upgrade install behaves as documented.

**Checks:**

```bash
PATH=".venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .
```

**Merge Point:** Merge as the release candidate for the rearchitecture.

---

## Manual HA Test Matrix

Run these before the final release merge:

- Fresh HA install from HACS with no optional groups enabled.
- Fresh HA install with current detail sensors enabled.
- Fresh HA install with forecast adapter sensors enabled.
- Fresh HA install with pollen enabled and authorized.
- Fresh HA install with pollen enabled and unauthorized.
- Fresh HA install with air quality enabled and authorized.
- Fresh HA install with air quality enabled and unauthorized.
- Fresh HA install with tropical summary enabled and no active storms.
- Upgrade from current released version with `extra_entities=False`.
- Upgrade from current released version with `extra_entities=True`.
- Dashboard gallery after optional card dependencies are installed.

Expected outcomes:

- Core `weather.twc` remains available in every case where current, daily, hourly, and alerts are authorized.
- Optional endpoint failures are isolated.
- Entity count is low by default.
- Disabled-by-default entities can be enabled manually.
- Demo dashboard documentation matches actual requirements.

## Risks and Mitigations

- **Risk:** Existing users may rely on current optional sensor entity IDs.
  - **Mitigation:** Preserve unique IDs where possible and use disabled-by-default for new installs instead of deleting existing entities.
- **Risk:** Config option split can surprise existing users.
  - **Mitigation:** Add migration from `extra_entities` to new grouped options.
- **Risk:** Optional endpoint coordinators increase setup complexity.
  - **Mitigation:** Keep a shared base coordinator for endpoint fetch/error handling.
- **Risk:** Dashboard adapter sensors pull architecture back toward entity sprawl.
  - **Mitigation:** Treat card adapters as optional compatibility surfaces, not core entities.
- **Risk:** `CoordinatorWeatherEntity` migration could break weather forecast services.
  - **Mitigation:** Add tests around daily/hourly forecast service behavior and manual HA smoke tests.

## Definition of Done

- `weather.twc` is the single default enabled entity for a normal install.
- Core weather data refreshes independently from optional endpoint families.
- Optional endpoint failures are isolated and visible in diagnostics.
- Optional sensors are grouped, documented, and mostly disabled by default when high-cardinality or demo-specific.
- Fresh and upgraded HA instances behave as documented.
- Full project check passes.
- GitLab pipeline and GitHub mirror succeed.
