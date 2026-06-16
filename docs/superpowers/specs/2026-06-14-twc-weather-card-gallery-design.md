# TWC Weather Card Gallery Design

Date: 2026-06-14

## Goal

Create a Home Assistant demo dashboard that showcases the weather-card ecosystem from the SmartHomeScene “Top 10 Home Assistant Weather Cards” article using The Weather Company data wherever the card can consume it.

This dashboard is a gallery and compatibility demo. It should help us evaluate how well `weather.twc` and the integration's companion entities work with common Lovelace weather cards, while keeping third-party dependencies explicit.

Source article: https://smarthomescene.com/blog/top-10-home-assistant-weather-cards/

## Approved Direction

Use the approved **Hybrid Demo Dashboard** direction with a **Two-Phase** delivery model.

The dashboard should render what can be supported directly now, include card-specific YAML examples for the rest, and clearly label cards that need HACS resources, adapter/template entities, or non-TWC data sources.

## Audience

Primary audience:

- Users evaluating whether the integration works with popular Home Assistant weather cards.
- The project owner testing live TWC data in a local Home Assistant container.
- Future contributors who need a concrete compatibility target.

Secondary audience:

- README/GitLab visitors looking for a visual proof point.
- Maintainers deciding which integration entities or attributes to add next.

## Card Set

The gallery should cover these ten cards from the article:

- Home Assistant built-in Weather Forecast Card.
- `custom:simple-weather-card`.
- `custom:hourly-weather`.
- Animated Weather Card / BOM-style weather card family.
- `custom:weather-radar-card`.
- `custom:clock-weather-card`.
- `custom:meteoalarm-card`.
- Lovelace Horizon / Sun Card.
- `custom:ha-card-weather-conditions`.
- `custom:platinum-weather-card`.

## Data Sources

Primary TWC-backed sources:

- `weather.twc`.
- Weather attributes on `weather.twc`, including current conditions, daily forecast support, hourly forecast support, alert summaries, wind gust, UV index, cloud cover, humidity, pressure, visibility, and integration version.
- Optional companion sensors when the integration option is enabled:
  - `sensor.twc_alert_count`
  - `sensor.twc_condition_phrase`
  - `sensor.twc_observation_time`
  - `sensor.twc_integration_version`
  - `sensor.twc_wind_gust`

Allowed non-TWC sources:

- `sun.sun` for clock/sun/horizon cards.
- A radar provider required by the radar card, clearly labeled as not TWC-backed.

The dashboard must not fabricate weather data. If a card needs data the integration does not expose, the card should be labeled as requiring adapter entities or future integration work.

## Phase 1 Scope

Phase 1 is repo-first and low-risk.

In scope:

- Add a dashboard YAML gallery under `dashboards/`.
- Add setup documentation under `docs/`.
- Add a compatibility matrix documenting each card's resource name, expected entity inputs, TWC mapping, and status.
- Add template/helper YAML examples where cards expect sensor-style inputs instead of a weather entity.
- Keep the existing `dashboards/the-weather-company-demo.yaml` intact unless the new gallery needs to link to it.
- Add tests that parse the dashboard/catalog files and check expected entities, card names, and status labels are present.

Out of scope:

- Installing HACS.
- Downloading third-party card resources into the repo.
- Bundling third-party JavaScript cards.
- Changing the integration backend.
- Faking radar, sun, pollen, air-quality, or meteogram data.
- Making every third-party card render in the local HA instance.

## Phase 2 Scope

Phase 2 is live-demo setup in the local Home Assistant instance.

In scope:

- Install or register currently working third-party card resources in the HA demo container where feasible.
- Apply the gallery dashboard to the HA demo instance.
- Keep clear status notes for cards that are archived, incompatible, or require non-TWC sources.
- Update docs with tested card versions or resource URLs.

Out of scope:

- Committing downloaded third-party card assets unless the license and project direction explicitly allow it.
- Maintaining forks of third-party cards.
- Building a custom replacement for any listed third-party card.

## Dashboard Layout

The gallery should use a top-level vertical stack or dashboard view with these sections.

### 1. TWC Hero

Purpose: establish that the dashboard is using live The Weather Company data.

Content:

- Current state from `weather.twc`.
- Temperature and feels-like value.
- Alert status from `weather.twc` or `sensor.twc_alert_count`.
- Integration release version.
- A short note that third-party cards below are configured against TWC entities where possible.

### 2. Compatibility Summary

Purpose: make dependency status obvious before a user sees cards fail to render.

Statuses:

- `Live`: expected to render with built-in Home Assistant and current TWC entities.
- `Requires HACS card`: YAML is provided, but the frontend resource must be installed.
- `Requires adapter entities`: needs template/helper sensors.
- `Requires non-TWC source`: needs sun, radar, or another provider.
- `Research needed`: card may be archived, renamed, or incompatible with current Home Assistant.

### 3. Live-Ready Cards

Cards that should be configured first:

- Built-in Weather Forecast Card using `weather.twc`.
- Simple Weather Card using `weather.twc`.
- Hourly Weather Card using `weather.twc` hourly forecast support.
- Clock Weather Card using `weather.twc` and `sun.sun`.

### 4. Adapter-Backed Cards

Cards that should include YAML plus adapter notes:

- Animated Weather Card / BOM-style family.
- Weather Conditions Card.
- Platinum Weather Card.
- Meteoalarm-style alerts card using TWC alert count/headline data where supported.

Adapter entities should be named predictably and documented. For example:

- `sensor.twc_demo_condition`
- `sensor.twc_demo_temperature`
- `sensor.twc_demo_feels_like`
- `sensor.twc_demo_wind_speed`
- `sensor.twc_demo_wind_gust`
- `sensor.twc_demo_alert_summary`

### 5. Context Cards

Cards that are useful in a weather dashboard but are not fully TWC-backed:

- Horizon/Sun Card using `sun.sun`.
- Weather Radar Card using its required radar tile source.

These cards should remain in the gallery because the article includes them, but their dependency labels must be prominent.

## Error Handling And Degraded States

The dashboard and docs should handle missing pieces explicitly:

- If `weather.twc` does not exist, the docs should tell the user to replace the entity id.
- If optional companion sensors are disabled, adapter-backed sections should mention the integration option.
- If a card resource is not installed, the YAML should be documented as an example rather than silently failing.
- If a TWC field is unavailable, the UI should show `Unavailable` or a plain explanatory label such as `No gust reported`.
- If a listed card is archived or incompatible, its status should be `Research needed` or `Not installed`, not `Live`.

## Testing

Phase 1 tests should cover repository artifacts, not third-party rendering:

- Dashboard YAML parses.
- The gallery references `weather.twc`.
- All ten article cards are represented.
- The compatibility matrix contains each required status.
- The docs mention HACS/resource installation requirements.
- The docs identify non-TWC dependencies for radar and sun cards.

Phase 2 verification should be manual/browser-based in the HA demo instance:

- Apply the dashboard YAML.
- Confirm the built-in Weather Forecast Card renders with TWC data.
- Confirm installed third-party cards render or show expected missing-resource errors.
- Confirm status labels match actual installed state.

## Success Criteria

- A user can open one repo document and understand how each of the ten article cards maps to TWC data.
- The repo contains a dashboard YAML gallery that can be applied to Home Assistant.
- The existing TWC demo dashboard remains usable.
- No card presents fabricated data as real TWC data.
- The design leaves a clear path for later integration improvements if a popular card needs additional entities.
