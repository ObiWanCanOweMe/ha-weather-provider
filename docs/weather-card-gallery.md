# TWC Weather Card Gallery

This repo includes a Phase 1 Home Assistant Lovelace gallery for evaluating popular weather cards with The Weather Company data. The gallery YAML is a complete Home Assistant Sections view. Each weather-card demo is grouped with its descriptor in the same grid section so the context stays adjacent while each card remains its own editable dashboard object.

Gallery YAML:

- `dashboards/the-weather-company-card-gallery.yaml`

Dependency chain reference:

- `docs/weather-card-gallery-dependencies.md`

Source article:

- https://smarthomescene.com/blog/top-10-home-assistant-weather-cards/

## Expected Entity

The gallery expects this weather entity:

- `weather.twc`

If Home Assistant created a different entity id, replace every `weather.twc` reference in the YAML with the actual entity id before adding the gallery to a dashboard.

## Phase 1

Phase 1 is repo-only. It adds the gallery YAML and compatibility notes. It does not bundle third-party JavaScript, install HACS, or guarantee every custom card renders before its frontend resource is installed.

## Phase 2

Phase 2 is live Home Assistant setup. Install the custom cards, register frontend resources, apply the gallery dashboard, and update this document with the tested card versions and any card-specific compatibility notes.

Simple Weather Card v0.8.5 also needs `dashboards/resources/twc-simple-weather-card-compat.js` registered after its HACS resource in current Home Assistant builds. The shim keeps the card's older localization lookup compatible with modern Home Assistant frontend objects.

## Status Labels

- `Live`: expected to render with built-in Home Assistant and current TWC entities.
- `Installed via HACS`: verified in the test Home Assistant instance with a HACS-managed frontend resource.
- `Requires HACS card`: YAML is provided, but the frontend card resource must be installed.
- `Requires adapter entities`: needs optional integration sensors such as `sensor.twc_temperature`.
- `Requires non-TWC source`: needs `sun.sun`, RainViewer, or another provider; the data is not TWC-backed.
- `Research needed`: the card may be archived, renamed, incompatible, or may need live testing with the TWC alert model.
- `Adapter needed`: TWC has relevant source data, but the card expects another integration's entity schema.

## Compatibility Matrix

| Card | YAML Type | Status | TWC Mapping |
| --- | --- | --- | --- |
| Home Assistant Weather Forecast Card | `weather-forecast` | Live | Uses `weather.twc` directly |
| Simple Weather Card | `custom:simple-weather-card` | Installed via HACS | Uses `weather.twc` directly |
| Hourly Weather Card | `custom:hourly-weather` | Installed via HACS | Uses `weather.twc` hourly forecast |
| Animated Weather Card | `custom:bom-weather-card` | Requires adapter entities | Uses current detail sensors plus daily forecast adapter sensors |
| Weather Radar Card | `custom:weather-radar-card` | Requires non-TWC source | Uses RainViewer radar tiles; not TWC-backed |
| Clock Weather Card | `custom:clock-weather-card` | Installed via HACS | Uses `weather.twc` and `sun.sun` |
| Meteoalarm Card | Built-in `entities` placeholder | Adapter needed | TWC alert count/summary data needs an adapter before `custom:meteoalarm-card` can render it |
| Lovelace Horizon Card | `custom:horizon-card` | Requires non-TWC source | Uses Home Assistant sun/moon context; not TWC-backed |
| Weather Conditions Card | `custom:ha-card-weather-conditions` | Requires adapter entities | Uses core TWC weather values through optional integration sensors |
| Platinum Weather Card | `custom:platinum-weather-card` | Requires adapter entities | Uses `weather.twc` plus optional integration sensors |

## Optional Adapter Entities

Some cards expect individual sensor entities instead of a single weather entity. Enable the integration's current detail sensors before using current-condition adapter cards.

Expected generated entities include:

- `sensor.twc_condition_phrase`
- `sensor.twc_temperature`
- `sensor.twc_feels_like_temperature`
- `sensor.twc_humidity`
- `sensor.twc_pressure`
- `sensor.twc_wind_speed`
- `sensor.twc_wind_bearing`
- `sensor.twc_wind_gust`
- `sensor.twc_alert_count`

These are created by the integration's current detail sensors option, not by dashboard-local template helpers.

The Animated Weather Card forecast rows use the integration's optional daily forecast adapter sensors. Enable forecast adapter sensors to create these forecast entities:

- `sensor.twc_daily_forecast_day_1_condition`
- `sensor.twc_daily_forecast_day_1_high`
- `sensor.twc_daily_forecast_day_1_low`
- `sensor.twc_daily_forecast_day_1_precip_probability`
- `sensor.twc_daily_forecast_day_1_precip_amount`
- `sensor.twc_daily_forecast_day_1_summary`

The same six-entity pattern repeats for days 2 through 5. Forecast adapter sensors are disabled by default after creation because they are high-cardinality compatibility entities; enable the specific entities you need from Home Assistant's entity registry.

## Non-TWC Dependencies

The Lovelace Horizon Card depends on Home Assistant's sun/moon context. The Weather Radar Card depends on RainViewer radar tiles. These are useful weather-dashboard context cards, but they are not TWC-backed and should not be presented as Weather Company API data.

## How To Add The Gallery

1. Install any third-party cards you want to render.
2. Register their frontend resources in Home Assistant.
3. Enable the integration's current detail sensors and forecast adapter sensors if you want to test adapter-backed cards.
4. Open Home Assistant.
5. Go to the dashboard raw configuration editor or storage-backed dashboard import path.
6. Add the contents of `dashboards/the-weather-company-card-gallery.yaml` as a full Sections view configuration.
7. Save the dashboard.

Cards whose frontend resources are missing will show Home Assistant custom-card errors. That is expected during Phase 1.
