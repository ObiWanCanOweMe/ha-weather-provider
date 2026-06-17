# The Weather Company for Home Assistant

Custom Home Assistant integration for The Weather Company API. The integration creates a `weather.twc` entity backed by TWC current conditions, daily forecasts, hourly forecasts, and alert headlines, with optional companion sensors for richer dashboards.

## Features

- Weather entity for current conditions and forecasts.
- Config flow setup with API key, latitude, longitude, units, and language.
- Configurable refresh interval, daily forecast duration, and hourly forecast duration.
- Optional current-detail sensors for current-condition values, alert counts, observation time, and integration version.
- Optional forecast adapter sensors for custom dashboard cards that require per-day sensor entities.
- Optional packages for pollen, air quality, and tropical weather when your TWC API key is entitled for those endpoints.
- Redacted diagnostics for Home Assistant issue reporting.
- Demo dashboard YAML and weather card gallery YAML.

## Requirements

- Home Assistant `2026.3.2` or newer.
- A The Weather Company API key with access to the required Standard Weather Data endpoints.
- Required TWC endpoints:
  - `/v3/wx/observations/current`
  - `/v3/wx/forecast/daily/<duration>`
  - `/v3/wx/forecast/hourly/<duration>`
  - `/v3/alerts/headlines`

Optional endpoints are requested only when enabled in the integration options. See [Operations](docs/operations.md) for endpoint and entitlement behavior.

## Automatic Installation

Use HACS as a custom repository after this project is mirrored to a public GitHub repository.

HACS does not support GitLab-hosted custom repositories. Do not use the `git.kener.org` URL in HACS; it will not install from there. The repository URL must be a public GitHub repository URL. See [GitHub Mirror](docs/github-mirror.md) for the GitLab CI mirror setup.

1. Open Home Assistant.
2. Go to **HACS**.
3. Open the HACS menu and choose **Custom repositories**.
4. Add the public GitHub mirror URL:

   ```text
   https://github.com/ObiWanCanOweMe/ha-weather-provider
   ```

5. Select **Integration** as the category.
6. Install **The Weather Company**.
7. Restart Home Assistant.
8. Go to **Settings** > **Devices & services**.
9. Choose **Add integration** and search for **HA Weather Provider**.
10. Enter your TWC API key, latitude, longitude, units, language, and any optional entity groups you want created during setup.

After setup, Home Assistant should create the weather entity as:

```text
weather.twc
```

## Manual Installation

Use this path when HACS is not available.

1. Download or clone this repository.
2. Copy the integration directory into your Home Assistant config directory:

   ```text
   custom_components/ha_weather_provider
   ```

   The final path should look like:

   ```text
   <home-assistant-config>/custom_components/ha_weather_provider/manifest.json
   ```

3. Restart Home Assistant.
4. Go to **Settings** > **Devices & services**.
5. Choose **Add integration** and search for **HA Weather Provider**.
6. Enter your TWC API key, latitude, longitude, units, language, and any optional entity groups you want created during setup.

To update manually, replace the existing `custom_components/ha_weather_provider` directory with the newer version and restart Home Assistant.

## Configuration

The config flow asks for:

- **API Key**: Your The Weather Company API key.
- **Latitude**: Decimal degrees. North is positive, south is negative.
- **Longitude**: Decimal degrees. East is positive, west is negative.
- **Units**: TWC unit system.
- **Language**: TWC response language.
- **Install options**: Forecast durations, update interval, current detail sensors, forecast adapter sensors, pollen, air quality, and tropical weather.

The integration intentionally asks for latitude and longitude instead of only using Home Assistant's configured location, which makes it easy to demo or monitor a specific place.

## Options

These choices are available during initial setup and can be changed later from **Settings** > **Devices & services**.

Available options include:

- **Update interval**: Default refresh interval is 30 minutes.
- **Daily forecast duration**: Default is `7day`.
- **Hourly forecast duration**: Default is `2day`.
- **Create current detail sensors**: Adds individual current-condition sensors for dashboards and automations.
- **Create forecast adapter sensors**: Adds per-day forecast adapter sensors for custom dashboard cards. These high-cardinality entities are disabled by default after creation and can be enabled individually in Home Assistant.
- **Enable pollen forecast**: Requests TWC pollen forecast and U.S. pollen observation endpoints.
- **Enable air quality**: Requests the TWC global air quality endpoint.
- **Enable tropical weather**: Requests compact active tropical storm summary data.

Optional endpoint failures caused by missing entitlement, no data, or auth-style unavailability do not break the core `weather.twc` entity. Unexpected request failures still fail the coordinator update so they can be investigated.

## Upgrades

Existing installs are migrated automatically by Home Assistant when the integration loads. Older entries that used the former **Create optional extra entities** setting are mapped to the newer **Create current detail sensors** and **Create forecast adapter sensors** options so previously exposed companion entities continue to load.

The rearchitecture keeps the `weather.twc` unique ID and companion sensor unique IDs stable. This release does not intentionally retire older entity unique IDs, so it does not perform broad entity registry cleanup or delete user-customized entities.

## Dashboards

This repository includes two dashboard examples:

- `dashboards/the-weather-company-demo.yaml`
- `dashboards/the-weather-company-card-gallery.yaml`

The demo dashboard is documented in [Demo Dashboard Card](docs/dashboard-demo.md).

The card gallery is documented in [TWC Weather Card Gallery](docs/weather-card-gallery.md), with dependency notes in [Weather Card Gallery Dependencies](docs/weather-card-gallery-dependencies.md).

Both dashboards expect:

```text
weather.twc
```

If Home Assistant creates a different entity id, update the YAML references before adding the dashboard.

## Troubleshooting

- If the integration does not appear after installation, restart Home Assistant and clear the browser cache.
- If optional sensors are unavailable, confirm the matching option is enabled and that your TWC API key is entitled for that endpoint package.
- If a dashboard card shows a custom-card error, install the required HACS frontend card and register its resource.
- If `weather.twc` was previously created with a different entity id, remove and re-add the integration or rename the entity in Home Assistant.

## Local Development

Install development dependencies:

```bash
python3 -m pip install -r requirements-dev.txt
```

Run the test suite:

```bash
python3 -m pytest
```

Run the project harness:

```bash
python3 path/to/obi-dev-harness/scripts/harness.py project-check .
```

Start a local Home Assistant development instance:

```bash
scripts/develop
```

## Project Links

- Documentation: https://git.kener.org/my-projects/ha-weather-provider
- Issues: https://git.kener.org/my-projects/ha-weather-provider/-/issues
