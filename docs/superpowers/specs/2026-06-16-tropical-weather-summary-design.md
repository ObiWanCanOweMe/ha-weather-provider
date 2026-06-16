# Tropical Weather Summary Design

## Goal

Add a compact, optional tropical weather slice for The Weather Company active storm data. The first milestone should answer one dashboard question: are there active tropical systems, and what are their high-level details?

This slice intentionally avoids per-storm entities, forecast cones, projected paths, raw bulletins, and model tracks. Those endpoints depend on storm identifiers and should be later milestones after the active storm list is stable.

## API Scope

Use the TWC Tropical Current Position endpoint:

`/v2/tropical/currentposition`

Request parameters:

- `source=default`
- `basin=all`
- `format=json`
- `units=<configured units>`
- `language=<configured language>`
- `nautical=false`
- `apiKey=<configured API key>`

The endpoint is optional. The integration must treat `401`, `403`, `204`, and empty/no-active-storm responses as non-fatal when tropical weather is enabled. The existing weather entity must continue loading even when the tropical endpoint is unavailable or not included in the API package.

## Options

Add a config entry option:

- `enable_tropical_weather`

Default is `false`. When disabled, no tropical endpoint is requested and no tropical sensors are created.

## Data Model

Extend coordinator data with a `tropical_current_position` payload defaulting to an empty dictionary. When enabled, fetch the tropical endpoint after the required weather payloads succeed.

Normalize active storm records into compact storm summaries:

- `storm_id`
- `storm_key`
- `name`
- `basin`
- `type`
- `category`
- `latitude`
- `longitude`
- `max_sustained_wind`
- `wind_gust`
- `minimum_pressure`
- `movement_direction`
- `movement_speed`
- `advisory_time`
- `expires`
- `headline`

Normalization should tolerate both absent values and list-shaped headline fields.

## Entities

Create tropical sensors only when `enable_tropical_weather` is enabled:

- `sensor.twc_tropical_active_storm_count`
- `sensor.twc_tropical_active_storms`
- `sensor.twc_tropical_last_update_time`, only if a useful advisory or process time can be derived
- `sensor.twc_tropical_expiration_time`, only if expiration data can be derived

`sensor.twc_tropical_active_storm_count` is numeric.

`sensor.twc_tropical_active_storms` uses a short state:

- `No active storms`
- `1 active storm`
- `<N> active storms`

It exposes the normalized storm summaries as attributes rather than creating per-storm entities. This keeps the entity registry stable as storms appear, disappear, or change identifiers.

## Error Handling

Tropical data must be entitlement-safe:

- Required weather data failures keep their current behavior.
- Tropical `401`, `403`, `204`, and no-data responses produce an empty tropical payload.
- Other tropical request failures should not prevent core weather setup, but should be logged clearly as optional tropical endpoint failures.

This matches the pollen pattern and prevents optional endpoint access from breaking `weather.twc`.

## Dashboard Behavior

The card gallery can add a small tropical summary row or diagnostic card later:

- Show active storm count.
- Show the compact active storm summary state.
- Do not imply cone, track, or bulletin support in this slice.

## Tests

Add tests for:

- API client calls the expected tropical current-position endpoint and parameters.
- Optional tropical endpoint returns empty payload for no-data and entitlement failures.
- Coordinator fetches tropical data only when enabled.
- Coordinator keeps required weather data available when tropical data is unavailable.
- Options flow persists `enable_tropical_weather`.
- Sensor setup creates tropical sensors only when enabled.
- Sensor values map populated active storm payloads.
- Sensors show empty/no-active-storm state for empty or missing payloads.

## Follow-Up Milestones

Later tropical slices can use active storm identifiers to add:

- Projected path summary
- Forecast cone metadata
- Raw bulletin summary
- Tropical model storm list and model detail
- Optional dashboard map support
