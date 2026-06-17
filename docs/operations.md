# Operations

## Default refresh interval

The integration uses Home Assistant's `DataUpdateCoordinator` and polls The Weather Company APIs. The default refresh interval is 30 minutes.

The options flow can change the refresh interval within the supported limits exposed by the integration. Keep the interval high enough to respect account quotas and avoid unnecessary Home Assistant updates.

## Required endpoints

Every refresh requests the core weather payloads:

- Current observations: `/v3/wx/observations/current`
- Daily forecast: `/v3/wx/forecast/daily/<duration>`
- Hourly forecast: `/v3/wx/forecast/hourly/<duration>`
- Alert headlines: `/v3/alerts/headlines`

The daily and hourly duration path segments come from integration options. The default daily duration is `7day`; the default hourly duration is `2day`.

## Optional endpoints

Optional endpoints are requested only when their options are enabled:

- Pollen forecast: `/v2/indices/pollen/daypart/<duration>`
- U.S. pollen observation: `/v1/geocode/<latitude>/<longitude>/observations/pollen.json`
- Tropical current position: `/v2/tropical/currentposition`
- Global air quality: `/v3/wx/globalAirQuality`

Optional endpoint failures caused by missing entitlement, no data, or auth-style unavailability do not break the main `weather.twc` entity. The integration keeps core weather data available, stores an empty optional payload for that endpoint, and related optional sensors expose no value or endpoint-specific empty states when no usable data is returned.

Unexpected optional request failures reported as `TWCRequestError` raise a coordinator update failure instead of being silently swallowed. Treat those errors as real refresh failures that should be investigated separately from normal optional endpoint entitlement or data availability.

## API key entitlement

The Weather Company API keys can be entitled for different endpoint packages. A key can work for current observations, daily forecasts, hourly forecasts, and alert headlines while not being entitled for pollen, tropical weather, air quality, or other optional packages. When an optional package is not entitled, disable that option or expect the corresponding optional payload to remain empty; related sensors may expose no value or endpoint-specific empty states.

## Upgrade behavior

Home Assistant runs the integration config entry migration automatically when an older entry loads. Entries created before the optional sensor surface was split can contain the legacy `extra_entities` option. During migration, `extra_entities: true` is mapped to both `current_detail_sensors: true` and `forecast_adapter_sensors: true`; `extra_entities: false` or a missing value maps both newer options to `false`.

The legacy option is preserved during migration for compatibility, but the current options flow only writes the newer grouped options. Once a user saves options after upgrading, Home Assistant stores the grouped shape.

No entity unique IDs are intentionally retired by this migration. The weather entity remains `weather.twc` for fresh installs, existing unique IDs are preserved, and the integration does not perform broad entity registry cleanup. If a future release retires entities, cleanup should be narrowly scoped to known integration-owned unique IDs and documented here.

## Polling model

The Weather Company Standard Weather Data package is polled over HTTPS. The integration uses request/response API calls and does not use webhooks or MQTT.

## Local development

The `scripts/develop` helper starts Home Assistant with `custom_components` on `PYTHONPATH`, matching the custom integration layout used by common blueprint repositories.

## HACS metadata

The repository includes `hacs.json` to declare the integration display name and minimum Home Assistant/HACS versions for future HACS distribution.
