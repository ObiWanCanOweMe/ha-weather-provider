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

## Polling model

The Weather Company Standard Weather Data package is polled over HTTPS. The integration uses request/response API calls and does not use webhooks or MQTT.
