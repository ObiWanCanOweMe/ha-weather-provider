# TWC Weather Integration Design

Date: 2026-06-12

## Goal

Build the first functional Home Assistant weather integration backed by The Weather Company Standard Weather Data package.

The first version will create one weather entity per config entry and expose current conditions plus a 7-day daily forecast. Hourly forecast support is intentionally deferred and should be tracked as a later GitLab milestone.

## Scope

In scope:

- Config flow for one TWC-backed weather entity.
- Explicit user-provided latitude and longitude.
- Explicit unit selection using TWC unit codes.
- Optional language setting, defaulting to `en-US`.
- Current conditions from TWC Currents On Demand.
- 7-day daily forecast from TWC Daily Forecast.
- Home Assistant weather entity mapping for current fields and daily forecasts.
- Error handling for common TWC HTTP responses.
- Tests around config validation, API client behavior, coordinator updates, and entity mapping.

Out of scope:

- Hourly forecast implementation.
- Multiple entities or multiple locations per config entry.
- Weather alerts.
- PWS-specific endpoints.
- Location search or geocoding through TWC.
- API aggregation engine usage.

## API References

Base host:

- `https://api.weather.com`

Primary endpoints:

- `GET /v3/wx/observations/current`
- `GET /v3/wx/forecast/daily/7day`

Common query parameters:

- `apiKey`: TWC API key.
- `geocode`: latitude and longitude in `lat,lon` order.
- `units`: one of `e`, `m`, `h`, or `s`.
- `language`: language code such as `en-US`.
- `format`: `json`.

Requests must use HTTPS and should request gzip-compressed responses. Cache behavior should respect TWC `Cache-Control: max-age=...` headers when practical.

## Configuration

The config flow will ask for:

- API key.
- Latitude.
- Longitude.
- Units.
- Language.

Validation rules:

- API key must be non-empty.
- Latitude must be numeric and between `-90` and `90`.
- Longitude must be numeric and between `-180` and `180`.
- Units must be one of:
  - `e`: English.
  - `m`: Metric.
  - `h`: Hybrid UK.
  - `s`: Metric SI.
- Language defaults to `en-US` and must be non-empty.

The config entry title should be derived from the configured coordinates, for example `TWC Weather 40.5800,-111.6600`.

## Architecture

Add a small TWC API client module responsible for:

- Building URLs and query parameters.
- Sending requests through Home Assistant's aiohttp client session.
- Supplying `Accept-Encoding: gzip`.
- Parsing JSON responses.
- Translating relevant HTTP failures into integration-specific exceptions.

Add a `DataUpdateCoordinator` responsible for:

- Fetching current conditions and daily forecast together.
- Storing the latest combined data payload.
- Raising `UpdateFailed` for temporary or recoverable failures.
- Using a conservative update interval appropriate for weather data and API usage.

Keep `WeatherEntity` focused on Home Assistant mapping:

- Read current condition values from coordinator data.
- Convert TWC units and condition values into Home Assistant weather properties.
- Implement daily forecast support from the 7-day forecast payload.

## Data Flow

1. User creates the integration through the config flow.
2. Home Assistant stores API key, coordinates, units, and language in the config entry.
3. Integration setup creates a TWC client and coordinator.
4. Coordinator performs the first refresh before adding the entity.
5. Weather entity reads all current and forecast values from coordinator data.
6. Later refreshes update the coordinator and notify the entity.

## Error Handling

Handle TWC responses as follows:

- `204`: no data for the configured location; surface as a Home Assistant update failure.
- `400`: invalid request; likely configuration or client bug.
- `401`: invalid or missing API key.
- `403`: API key is valid but lacks access to the requested endpoint.
- `404`: endpoint not found.
- `405`: incorrect HTTP method; client bug.
- `406`: request did not accept supported compression or format.
- `408`: request timeout; retry on later coordinator refresh.
- `500`, `502`, `503`, `504`: temporary service failure; retry on later coordinator refresh.

Config flow validation should attempt a lightweight current conditions request so bad credentials, unauthorized package access, and invalid coordinates are caught before entry creation.

## Testing

Recommended tests:

- Config flow accepts valid input and creates one entry.
- Config flow rejects invalid latitude, longitude, unit, and empty API key values.
- Config flow maps TWC `401` and `403` into user-visible errors.
- API client builds the expected current and daily forecast requests.
- API client handles `204`, `401`, `403`, and `5xx` responses.
- Coordinator combines current and daily forecast payloads.
- Weather entity exposes current temperature, humidity, pressure, wind, condition, and daily forecast data from representative TWC responses.

## Deferred Milestone

Create a GitLab milestone named `Hourly Forecast` after the repo is GitLab-backed. The milestone should cover adding TWC hourly forecast support through `/v3/wx/forecast/hourly/...`, including entity support, config or options behavior if needed, and tests.
