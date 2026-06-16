# TWC Weather Card Gallery

This repo includes a Phase 1 Home Assistant Lovelace gallery for evaluating popular weather cards with The Weather Company data. The gallery YAML is a complete Home Assistant Sections view. Each weather-card demo is grouped with its descriptor in the same grid section so the context stays adjacent while each card remains its own editable dashboard object.

Gallery YAML:

- `dashboards/the-weather-company-card-gallery.yaml`

Optional template helper examples:

- `docs/examples/twc-weather-card-gallery-template-sensors.yaml`

Dependency chain reference:

- `docs/weather-card-gallery-dependencies.md`

Source article:

- https://smarthomescene.com/blog/top-10-home-assistant-weather-cards/

## Expected Entity

The gallery expects this weather entity:

- `weather.twc`

If Home Assistant created a different entity id, replace every `weather.twc` reference in the YAML and template helper examples with the actual entity id before adding the gallery to a dashboard.

## Phase 1

Phase 1 is repo-only. It adds the gallery YAML, compatibility notes, and optional template helper examples. It does not bundle third-party JavaScript, install HACS, or guarantee every custom card renders before its frontend resource is installed.

## Phase 2

Phase 2 is live Home Assistant setup. Install the custom cards, register frontend resources, apply the gallery dashboard, and update this document with the tested card versions and any card-specific compatibility notes.

Simple Weather Card v0.8.5 also needs `dashboards/resources/twc-simple-weather-card-compat.js` registered after its HACS resource in current Home Assistant builds. The shim keeps the card's older localization lookup compatible with modern Home Assistant frontend objects.

## Status Labels

- `Live`: expected to render with built-in Home Assistant and current TWC entities.
- `Installed via HACS`: verified in the test Home Assistant instance with a HACS-managed frontend resource.
- `Requires HACS card`: YAML is provided, but the frontend card resource must be installed.
- `Requires adapter entities`: needs template/helper sensors such as `sensor.twc_demo_temperature`.
- `Requires non-TWC source`: needs `sun.sun`, RainViewer, or another provider; the data is not TWC-backed.
- `Research needed`: the card may be archived, renamed, incompatible, or may need live testing with the TWC alert model.
- `Adapter needed`: TWC has relevant source data, but the card expects another integration's entity schema.

## Compatibility Matrix

| Card | YAML Type | Status | TWC Mapping |
| --- | --- | --- | --- |
| Home Assistant Weather Forecast Card | `weather-forecast` | Live | Uses `weather.twc` directly |
| Simple Weather Card | `custom:simple-weather-card` | Installed via HACS | Uses `weather.twc` directly |
| Hourly Weather Card | `custom:hourly-weather` | Installed via HACS | Uses `weather.twc` hourly forecast |
| Animated Weather Card | `custom:bom-weather-card` | Requires adapter entities | Uses `sensor.twc_demo_*` current helpers plus integration-provided daily forecast adapter sensors |
| Weather Radar Card | `custom:weather-radar-card` | Requires non-TWC source | Uses RainViewer radar tiles; not TWC-backed |
| Clock Weather Card | `custom:clock-weather-card` | Installed via HACS | Uses `weather.twc` and `sun.sun` |
| Meteoalarm Card | Built-in `entities` placeholder | Adapter needed | TWC alert count/summary data needs an adapter before `custom:meteoalarm-card` can render it |
| Lovelace Horizon Card | `custom:horizon-card` | Requires non-TWC source | Uses Home Assistant sun/moon context; not TWC-backed |
| Weather Conditions Card | `custom:ha-card-weather-conditions` | Requires adapter entities | Uses core TWC weather values through template sensors |
| Platinum Weather Card | `custom:platinum-weather-card` | Requires adapter entities | Uses `weather.twc` plus template sensors |

## Optional Adapter Entities

Some cards expect individual sensor entities instead of a single weather entity. Use `docs/examples/twc-weather-card-gallery-template-sensors.yaml` as a starting point.

Expected generated entities include:

- `sensor.twc_demo_condition`
- `sensor.twc_demo_temperature`
- `sensor.twc_demo_feels_like`
- `sensor.twc_demo_humidity`
- `sensor.twc_demo_pressure`
- `sensor.twc_demo_wind_speed`
- `sensor.twc_demo_wind_bearing`
- `sensor.twc_demo_wind_gust`
- `sensor.twc_demo_alert_summary`

Enable the integration's optional extra entities if you also want current-condition sensors, compact diagnostic sensors, and daily forecast adapter sensors from the custom integration.

The Animated Weather Card forecast rows use the integration's optional daily forecast adapter sensors. Enable optional extra entities to create these forecast entities:

- `sensor.twc_daily_forecast_day_1_condition`
- `sensor.twc_daily_forecast_day_1_high`
- `sensor.twc_daily_forecast_day_1_low`
- `sensor.twc_daily_forecast_day_1_precip_probability`
- `sensor.twc_daily_forecast_day_1_precip_amount`
- `sensor.twc_daily_forecast_day_1_summary`

The same six-entity pattern repeats for days 2 through 5.

## Non-TWC Dependencies

The Lovelace Horizon Card depends on Home Assistant's sun/moon context. The Weather Radar Card depends on RainViewer radar tiles. These are useful weather-dashboard context cards, but they are not TWC-backed and should not be presented as Weather Company API data.

## How To Add The Gallery

1. Install any third-party cards you want to render.
2. Register their frontend resources in Home Assistant.
3. Add the optional template helpers if you want to test adapter-backed cards.
4. Open Home Assistant.
5. Go to the dashboard raw configuration editor or storage-backed dashboard import path.
6. Add the contents of `dashboards/the-weather-company-card-gallery.yaml` as a full Sections view configuration.
7. Save the dashboard.

Cards whose frontend resources are missing will show Home Assistant custom-card errors. That is expected during Phase 1.
