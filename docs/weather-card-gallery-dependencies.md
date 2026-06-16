# TWC Weather Card Gallery Dependencies

This document records the frontend cards, Home Assistant integrations, helper sensors, and external data sources needed by `dashboards/the-weather-company-card-gallery.yaml`. That YAML file is a complete Home Assistant Sections view. Each gallery item uses its own grid section so the descriptor card stays adjacent to the corresponding weather-card demo without wrapping the whole gallery in one nested `vertical-stack` card.

Operational polling and endpoint entitlement behavior is documented in [docs/operations.md](operations.md).

The test Home Assistant instance now uses HACS-managed resources for cards installed through HACS. Some remaining cards are still installed manually under `/config/www/community` with matching `/local/community/...` Lovelace resources.

## Test Instance Install Paths

| Dependency | Installed Path | Lovelace Resource |
| --- | --- | --- |
| Card Mod | `/config/www/community/lovelace-card-mod/card-mod.js` | `/local/community/lovelace-card-mod/card-mod.js` |
| Simple Weather Card | HACS-managed `kalkih/simple-weather-card` | `/hacsfiles/simple-weather-card/simple-weather-card-bundle.js?...` |
| Simple Weather Card compatibility shim | `/config/www/twc-simple-weather-card-compat.js` | `/local/twc-simple-weather-card-compat.js?...` |
| Hourly Weather Card | HACS-managed `decompil3d/lovelace-hourly-weather` | `/hacsfiles/lovelace-hourly-weather/hourly-weather.js?...` |
| Clock Weather Card | HACS-managed `pkissling/clock-weather-card` | `/hacsfiles/clock-weather-card/clock-weather-card.js?...` |
| Custom Animated Weather Card | `/config/www/community/bom-weather-card/bom-weather-card.js` | `/local/community/bom-weather-card/bom-weather-card.js` |
| Custom Animated Weather Card icons | `/config/www/icons/weather_icons/{animated,static}` | Referenced internally as `/local/icons/weather_icons/...` |
| Platinum Weather Card | `/config/www/community/platinum-weather-card/platinum-weather-card.js` plus release assets | `/local/community/platinum-weather-card/platinum-weather-card.js` |
| Weather Conditions Card | `/config/www/community/ha-card-weather-conditions/ha-card-weather-conditions.js` | `/local/community/ha-card-weather-conditions/ha-card-weather-conditions.js` |
| Horizon Card | `/config/www/community/lovelace-horizon-card/lovelace-horizon-card.js` | `/local/community/lovelace-horizon-card/lovelace-horizon-card.js` |
| Weather Radar Card | `/config/www/community/weather-radar-card/weather-radar-card.js` | `/local/community/weather-radar-card/weather-radar-card.js` |
| Meteoalarm Card | `/config/www/community/meteoalarm-card/meteoalarm-card.js` | `/local/community/meteoalarm-card/meteoalarm-card.js` |

The test instance has HACS installed and configured at `/config/custom_components/hacs`. For cards installed through HACS, keep only the `/hacsfiles/...` Lovelace resource entry active. Loading both a manual `/local/community/...` resource and a HACS `/hacsfiles/...` resource for the same card causes duplicate custom element registration errors in the browser.

Simple Weather Card v0.8.5 needs the local `twc-simple-weather-card-compat.js` shim in current Home Assistant builds. Load it after the HACS Simple Weather Card resource. The shim only patches the card's locale lookup so it can handle Home Assistant instances that expose `hass.localize()` without the older `hass.resources` map expected by the card bundle.

## Core TWC Chain

| Layer | Requirement | Current Source |
| --- | --- | --- |
| Weather entity | `weather.twc` | `ha_weather_provider` integration |
| Alert count | `sensor.twc_alert_count` | Optional extra entity from this integration |
| Current condition sensors | `sensor.twc_temperature`, `sensor.twc_feels_like_temperature`, `sensor.twc_dew_point`, `sensor.twc_humidity`, `sensor.twc_pressure`, `sensor.twc_pressure_change`, `sensor.twc_pressure_tendency_code`, `sensor.twc_pressure_tendency`, `sensor.twc_cloud_cover`, `sensor.twc_cloud_cover_phrase`, `sensor.twc_cloud_ceiling`, `sensor.twc_uv_index`, `sensor.twc_uv_description`, `sensor.twc_visibility`, `sensor.twc_wind_speed`, `sensor.twc_wind_gust`, `sensor.twc_wind_bearing`, `sensor.twc_precip_amount`, `sensor.twc_condition_phrase`, `sensor.twc_condition_code`, `sensor.twc_sunrise_time`, `sensor.twc_sunset_time` | Optional extra entities from this integration. `sensor.twc_cloud_ceiling` is exposed as a raw numeric value because TWC documentation says the unit varies by unit system, but live testing returned the same value across `e`, `m`, `h`, and `s`. |
| Daily forecast adapter helpers | `sensor.twc_daily_forecast_day_1_*` through `sensor.twc_daily_forecast_day_5_*` | Optional extra entities from this integration |
| Pollen sensors | `sensor.twc_pollen_grass_index`, `sensor.twc_pollen_grass_category`, `sensor.twc_pollen_tree_index`, `sensor.twc_pollen_tree_category`, `sensor.twc_pollen_ragweed_index`, `sensor.twc_pollen_ragweed_category`, `sensor.twc_pollen_forecast_time`, `sensor.twc_pollen_expiration_time`, `sensor.twc_pollen_observation_*` | Optional pollen forecast and U.S. pollen observation endpoints from this integration |
| Tropical weather summary sensors | `sensor.twc_tropical_active_storm_count`, `sensor.twc_tropical_active_storms`, `sensor.twc_tropical_last_update_time`, `sensor.twc_tropical_expiration_time` | Optional tropical current-position endpoint from this integration. The active-storm sensor keeps compact storm summaries in attributes instead of creating per-storm entities. |
| Air quality sensors | `sensor.twc_aq_index`, `sensor.twc_aq_category`, `sensor.twc_aq_primary_pollutant`, `sensor.twc_aq_*_amount`, `sensor.twc_aq_*_index`, `sensor.twc_aq_*_category` | Optional Air Quality Global endpoint from this integration |
| Forecasts | Daily and hourly weather forecast APIs | `weather.twc` forecast methods |

The integration's optional extra entities expose current-condition sensors and five days of daily forecast adapter sensors for condition, high, low, precipitation probability, precipitation amount, and summary. These replace the old card-gallery template helper sensors, so persistent entity names should use `sensor.twc_*` rather than a demo-specific namespace. A current precipitation-rate sensor is not exposed because the current TWC observation payload used by this integration does not provide a confirmed rate/intensity field.

## Card Dependency Chains

| Gallery Section | Frontend Card | Entity/Data Chain | Remaining Gap |
| --- | --- | --- | --- |
| Home Assistant Weather Forecast Card | Built in | `weather.twc` | None |
| Simple Weather Card | HACS `kalkih/simple-weather-card` | `weather.twc` | Installed in test HA; active resource is HACS-managed |
| Hourly Weather Card | HACS `decompil3d/lovelace-hourly-weather` | `weather.twc` hourly forecast | Installed in test HA; active resource is HACS-managed |
| Clock Weather Card | HACS `pkissling/clock-weather-card` | `weather.twc`; optional clock/timezone from HA | Installed in test HA; gallery YAML uses `forecast_rows` rather than old `forecast_days` |
| Custom Animated Weather Card | `DavidFW1960/bom-weather-card` | `sensor.twc_condition_phrase`, temperature, apparent temperature, humidity, pressure, wind bearing, wind speed, wind gust; `sensor.twc_daily_forecast_day_N_*`; local weather icon SVG assets | Uses integration-provided adapter sensors |
| Platinum Weather Card | `Makin-Things/platinum-weather-card` | `weather.twc` plus optional `sensor.twc_*` adapter sensors; bundled SVG/JS release assets | Some sections need additional entities for rainfall, fire danger, and extended forecast text |
| Weather Conditions Card | `r-renato/ha-card-weather-conditions` | optional `sensor.twc_*` current, pollen, and air quality sensors; optional `sun.sun` and moon phase context | Marine, lightning, camera, and some alert layers need extra integrations or TWC-derived sensors |
| Meteoalarm Card | `MrBartusek/MeteoalarmCard` | Installed frontend resource only | Needs a supported alert integration or a TWC alert adapter before the actual custom card can replace the placeholder |
| Horizon Card | `rejuvenate/lovelace-horizon-card` | Home Assistant location, `sun`, and optional `moon` integrations | Not TWC-backed; depends on HA sun/moon context. In current Home Assistant builds, Moon is config-entry based and cannot be enabled through YAML. |
| Weather Radar Card | `jpettitt/weather-radar-card` | External radar tile providers such as RainViewer, NOAA/NWS, or DWD | Not TWC-backed; network tile access required |

## Fork Candidates

These are worth evaluating for forks or vendored companion cards:

| Candidate | Reason |
| --- | --- |
| Simple Weather Card | Small surface area and direct weather entity consumption; a TWC-focused variant could avoid upstream compatibility churn. |
| Custom Animated Weather Card | Sensor-heavy configuration maps well to generated TWC adapter sensors, but the card is provider-generic and may need TWC naming defaults. |
| Platinum Weather Card | Richest demo surface, but has many assets and entity slots. A curated TWC preset or fork could reduce setup friction. |
| Weather Conditions Card | Good showcase for TWC enrichment. Pollen, U.S. pollen observation, and air quality sensors can be created when enabled and populate when endpoint data is returned. |
| Meteoalarm Card | Direct fork is less attractive than building a TWC alert adapter that emits a supported warning schema. |

Weather Radar Card and Horizon Card are less useful as forks for this integration because their primary data is not Weather Company API data.

## TWC Data Milestones

Air quality and pollen are intentionally separate milestones because they use separate TWC endpoint families and can fail independently based on API entitlement or regional data availability.

| Milestone | TWC Docs | Initial Entity Direction |
| --- | --- | --- |
| Air Quality | `docs/twc_api/API - Standard -  Air Quality - Global - v3.0.pdf` | Optional sensors for AQI, category, primary pollutant, pollutant concentrations/indexes where present |
| Pollen | `docs/twc_api/API - Standard - Lifestyle Indices - Pollen Index - v2.0.pdf`, `docs/twc_api/API - Standard US Pollen Observation v1.0.pdf`, `docs/twc_api/API - Standard - Pollen Historical - v3.pdf` | Implemented slices: optional forecast sensors for grass/tree/ragweed index and category, plus U.S.-only observation sensors for total/tree/grass/weed/mold count, index, description, report time, and expiration. Deferred: historical pollen trends if useful for a future dashboard. |
| Astronomy and Moon Data | `docs/twc_api/API - Standard - v3 - Forecast - Astronomy.pdf` | Optional astronomy sensors for sunrise, sunset, moonrise, moonset, moon phase, and related forecast values where present. Keep HA `sun`/`moon` integration context separate from TWC-backed data. |
| Lightning Proximity | `docs/twc_api/API - Standard - v3 - Lightning .pdf` | Optional sensors for nearby lightning activity, distance/bearing/proximity, and observation timing where endpoint access and geography support it. |
| Lifestyle Indices | `docs/twc_api/API - Standard - Lifestyle Indices - *.pdf` | Optional index sensors for useful demo/dashboard values such as driving difficulty, running, golf, mosquito, asthma/breathing, aches, frost, watering needs, dry skin, frizz, and related endpoint families. |
| Tropical Weather | `docs/twc_api/API - Standard - Tropical - *.pdf`, `docs/twc_api/API - Standard - v3 - Tropical Models - *.pdf` | First slice: optional compact active storm summary sensors from current-position data: `sensor.twc_tropical_active_storm_count`, `sensor.twc_tropical_active_storms`, `sensor.twc_tropical_last_update_time`, and `sensor.twc_tropical_expiration_time`. Later slices can add cone/path/bulletin/model detail. |
| Snow and Ski Conditions | `docs/twc_api/API - Standard - v3 - Snow and Ski Conditions.pdf` | Optional snow/ski condition sensors for resort-oriented snow-pack and ski-condition data if endpoint access and location lookup behavior are suitable. |

## Add-ons And Container Limits

The current test environment is a Home Assistant container, not Home Assistant OS or Supervised. Supervisor add-ons cannot be installed in this instance. File access, HACS installation, and frontend cards are managed directly through the mounted config directory instead.

The Moon integration is also not configured through YAML in this Home Assistant version. Add it through the Home Assistant UI if the Horizon Card moon layer is required for a demo.

## Source Repositories

- HACS: `hacs/integration`
- Card Mod: `thomasloven/lovelace-card-mod`
- Simple Weather Card: `kalkih/simple-weather-card`
- Hourly Weather Card: `decompil3d/lovelace-hourly-weather`
- Clock Weather Card: `pkissling/clock-weather-card`
- Custom Animated Weather Card: `DavidFW1960/bom-weather-card`
- Platinum Weather Card: `Makin-Things/platinum-weather-card`
- Weather Conditions Card: `r-renato/ha-card-weather-conditions`
- Horizon Card: `rejuvenate/lovelace-horizon-card`
- Weather Radar Card: `jpettitt/weather-radar-card`
- Meteoalarm Card: `MrBartusek/MeteoalarmCard`
