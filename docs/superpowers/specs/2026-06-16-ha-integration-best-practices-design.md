# HA Integration Best Practices Design

## Context

`docs/ha_integration_best_practices.txt` calls out two categories of work for this project:

- Keep the Home Assistant integration focused on getting data into Home Assistant, with API connectivity and parsing isolated in a Python library.
- Harden the integration around Home Assistant expectations: async I/O, config flow security, efficient polling, error handling, logging, tests, and community metadata.

The current integration works, but the boundary is too broad. `custom_components/ha_weather_provider/api.py` owns endpoint construction, request/status handling, and optional endpoint behavior. `weather.py` and `sensor.py` also contain reusable TWC payload normalization helpers mixed with Home Assistant entity code.

This design splits the work into two serial implementation plans so the structural refactor lands before the Home Assistant hardening pass.

## Plan 1: TWC Client Library Boundary

### Goal

Extract TWC API access and reusable payload normalization into a small Python package inside this repo, then make the Home Assistant integration consume that package.

The first plan should not change entity names, dashboard behavior, config flow UX, polling intervals, or optional endpoint semantics. It is a boundary refactor with tests.

### Package Shape

Add a package outside `custom_components`:

- `twc_weather_client/__init__.py`
- `twc_weather_client/client.py`
- `twc_weather_client/errors.py`
- `twc_weather_client/models.py`
- `twc_weather_client/normalizers.py`

The package owns:

- Base URL and endpoint paths.
- Query parameter construction.
- Async request execution through an injected `aiohttp.ClientSession`.
- TWC-specific status code mapping.
- TWC exception classes.
- Optional endpoint no-data helpers.
- Reusable normalization helpers for current conditions, forecasts, alerts, pollen, tropical summary, and air quality where they are not Home Assistant-specific.

The package does not own:

- Home Assistant config entries.
- Home Assistant entity classes.
- Home Assistant device classes, state classes, entity categories, or unit metadata.
- Lovelace dashboard YAML.
- Home Assistant update coordinator behavior.

### Integration Boundary

`custom_components/ha_weather_provider/api.py` should either disappear or become a compatibility shim that imports from `twc_weather_client`. The preferred final state is for integration modules to import the client package directly.

`coordinator.py` should remain responsible for deciding which optional endpoints to fetch based on config entry options.

`weather.py` and `sensor.py` should keep HA property methods and entity descriptions, but delegate shared parsing and series extraction to the client package where practical.

### Testing

Move or duplicate API-focused tests so the client package has direct unit tests for:

- Endpoint path construction.
- Required query parameters.
- Status code to exception mapping.
- Invalid JSON and non-object JSON payload handling.
- Optional no-data handling.
- Payload normalization helpers.

Keep HA integration tests for:

- Coordinator behavior.
- Entity behavior.
- Options flow behavior.
- Dashboard YAML references.

### Acceptance Criteria

- Existing public integration behavior is unchanged.
- Required weather data, optional pollen, tropical, and air quality behavior remain covered by tests.
- The Home Assistant integration no longer owns raw TWC API request implementation.
- Full project checks pass.

## Plan 2: HA Integration Hardening

### Goal

After the client boundary lands, align the Home Assistant layer with the remaining recommendations from `docs/ha_integration_best_practices.txt`.

This plan should use the cleaner boundary from Plan 1 rather than refactoring API logic and HA behavior at the same time.

### Manifest Metadata

Update `custom_components/ha_weather_provider/manifest.json` with appropriate Home Assistant metadata:

- `iot_class`: `cloud_polling`
- `integration_type`: `service`
- `issue_tracker`: GitLab project issue URL if available
- `codeowners`: project owner handle if one should be declared

Keep `version`, `documentation`, and `config_flow` intact unless a specific value is wrong.

### Diagnostics

Add `custom_components/ha_weather_provider/diagnostics.py`.

Diagnostics should include useful support context:

- Integration version.
- Configured unit system.
- Forecast durations.
- Update interval.
- Enabled optional endpoint flags.
- Whether latest coordinator payloads have current, daily, hourly, alerts, pollen, tropical, and air quality sections.
- Entity counts or enabled sensor groups if practical.

Diagnostics must redact:

- API key.
- Any future credential-like fields.
- Raw payload fields that could expose secrets.

### Optional Endpoint Handling

Make optional endpoint behavior consistent:

- Entitlement failures and documented no-data responses should not break core weather updates.
- Optional endpoint unavailability should produce debug or warning logs that identify the endpoint class without exposing the API key.
- Required endpoint auth and permission failures should still fail setup/update clearly.

This applies to existing optional endpoints:

- Alerts no-data behavior.
- Pollen forecast and observation.
- Tropical current position.
- Air quality.

### Polling and Quota Documentation

Document operational expectations:

- Default update interval.
- Configurable update interval limits.
- Which endpoints are called on each refresh when each option is enabled.
- Why the integration uses polling.
- Expected behavior when an API key lacks access to optional packages.

The likely homes are `docs/testing.md`, `docs/weather-card-gallery-dependencies.md`, or a new support-oriented doc if that reads cleaner.

### Repository Hygiene

Check whether generated files are tracked:

- `custom_components/ha_weather_provider/__pycache__/`
- `tests/__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`

If any are tracked, remove them from git and make sure `.gitignore` covers them.

### Testing

Add tests for:

- Diagnostics redaction.
- Diagnostics summary shape.
- Manifest metadata if the current test style supports it.
- Optional endpoint failures staying non-fatal.
- Required endpoint auth/permission failures remaining fatal.

### Acceptance Criteria

- The integration exposes diagnostics without leaking secrets.
- Manifest metadata better matches Home Assistant conventions for a cloud polling service.
- Optional endpoint behavior is predictable and documented.
- Generated cache files are not tracked.
- Full project checks pass.

## Serial Execution Rule

Plan 2 should not start until Plan 1 is merged. If Plan 1 reveals that a hardening item belongs in the client package rather than the HA integration, move that item into the client package before starting Plan 2.
