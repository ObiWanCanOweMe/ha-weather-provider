# TWC Weather Card Gallery

This repo includes a Phase 1 Home Assistant Lovelace gallery for evaluating popular weather cards with The Weather Company data.

Gallery YAML:

- `dashboards/the-weather-company-card-gallery.yaml`

Optional template helper examples:

- `docs/examples/twc-weather-card-gallery-template-sensors.yaml`

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

## Status Labels

- `Live`: expected to render with built-in Home Assistant and current TWC entities.
- `Requires HACS card`: YAML is provided, but the frontend card resource must be installed.
- `Requires adapter entities`: needs template/helper sensors such as `sensor.twc_demo_temperature`.
- `Requires non-TWC source`: needs `sun.sun`, RainViewer, or another provider; the data is not TWC-backed.
- `Research needed`: the card may be archived, renamed, incompatible, or may need live testing with the TWC alert model.

## Compatibility Matrix

| Card | YAML Type | Status | TWC Mapping |
| --- | --- | --- | --- |
| Home Assistant Weather Forecast Card | `weather-forecast` | Live | Uses `weather.twc` directly |
| Simple Weather Card | `custom:simple-weather-card` | Requires HACS card | Uses `weather.twc` directly |
| Hourly Weather Card | `custom:hourly-weather` | Requires HACS card | Uses `weather.twc` hourly forecast |
| Animated Weather Card | `custom:bom-weather-card` | Requires adapter entities | Uses `sensor.twc_demo_*` template sensors |
| Weather Radar Card | `custom:weather-radar-card` | Requires non-TWC source | Uses RainViewer radar tiles; not TWC-backed |
| Clock Weather Card | `custom:clock-weather-card` | Requires HACS card | Uses `weather.twc` and `sun.sun` |
| Meteoalarm Card | `custom:meteoalarm-card` | Research needed | TWC alert count/headline data may need an adapter |
| Lovelace Horizon Card | `custom:sun-card` | Requires non-TWC source | Uses `sun.sun`; not TWC-backed |
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

Enable the integration's optional extra entities if you also want the compact diagnostic sensors from the custom integration.

## Non-TWC Dependencies

The Lovelace Horizon Card depends on Home Assistant's `sun.sun` entity. The Weather Radar Card depends on RainViewer radar tiles. These are useful weather-dashboard context cards, but they are not TWC-backed and should not be presented as Weather Company API data.

## How To Add The Gallery

1. Install any third-party cards you want to render.
2. Register their frontend resources in Home Assistant.
3. Add the optional template helpers if you want to test adapter-backed cards.
4. Open Home Assistant.
5. Go to a dashboard.
6. Choose **Edit dashboard**.
7. Add a manual card.
8. Paste the contents of `dashboards/the-weather-company-card-gallery.yaml`.
9. Save the dashboard.

Cards whose frontend resources are missing will show Home Assistant custom-card errors. That is expected during Phase 1.
