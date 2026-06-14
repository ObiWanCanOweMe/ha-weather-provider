# Forecast Duration Options Design

## Context

The Weather Company Standard Weather Data package exposes forecast duration as part of the endpoint path. Daily forecast durations are separate 3, 5, 7, 10, and 15 day endpoints. Hourly forecast durations are separate 6 hour, 12 hour, 1 day, 2 day, 3 day, 10 day, and 15 day endpoints. Existing integration behavior is fixed to daily `7day` and hourly `2day`.

## Design

Add two config entry options:

- `daily_forecast_duration`, default `7day`
- `hourly_forecast_duration`, default `2day`

The defaults preserve existing behavior for current users and for newly configured entries. The options flow exposes both as bounded select fields using only documented TWC duration path segments.

The API client stores the selected durations and builds forecast endpoint paths from a small helper instead of fixed constants. Current conditions, alerts, units, language, and Home Assistant forecast mapping stay unchanged.

## Validation

The initial config flow keeps validating the default endpoints during setup. The options flow stores selected durations from fixed choices. Since TWC authorization is per endpoint and can vary by key, the coordinator's next refresh will surface endpoint authorization failures through the existing update failure path if a selected duration is not entitled.

## Testing

Tests cover:

- default daily and hourly endpoint paths remain `7day` and `2day`
- custom daily and hourly durations call the selected endpoint paths
- options flow stores selected durations with existing options
- setup passes selected durations into `TWCClient`
- invalid stored duration options fall back to defaults during setup
