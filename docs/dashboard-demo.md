# Demo Dashboard Card

This repo includes a Home Assistant Lovelace demo card for showcasing the HA Weather Provider integration.

Demo YAML:

- `dashboards/the-weather-company-demo.yaml`

## Expected Entity

The card expects this weather entity:

- `weather.the_weather_company`

If Home Assistant created a different entity id, replace every `weather.the_weather_company` reference in the YAML with the actual entity id before adding the card to a dashboard.

## How To Add It

1. Open Home Assistant.
2. Go to a dashboard.
3. Choose **Edit dashboard**.
4. Add a manual card.
5. Paste the contents of `dashboards/the-weather-company-demo.yaml`.
6. Save the dashboard.

## What It Shows

The card is designed for demos and screenshots. It shows:

- Current condition and live API status.
- Atmosphere values: humidity, pressure, visibility, and wind.
- Comfort and sky values: dew point, cloud cover, UV index, and wind gust.
- Integration coverage for shipped and planned features.
- Built-in hourly and daily forecast cards.
- A note about enriched daily forecast fields.

## Planned Milestones

Weather alerts and optional extra weather entities are shown as planned milestone labels only. They are not live alert or sensor data.

## Fallback Behavior

Some values may show as `Unavailable` if the running integration version does not expose that field yet or if Home Assistant does not surface it as a Lovelace-accessible weather attribute.
