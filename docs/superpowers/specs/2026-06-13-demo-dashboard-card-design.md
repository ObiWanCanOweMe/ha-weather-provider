# Demo Dashboard Card Design

Date: 2026-06-13

## Goal

Create a Home Assistant Lovelace dashboard card that demos the HA Weather Provider integration clearly during a screen share, README walkthrough, or development review.

The card should make the integration's value obvious at a glance: The Weather Company data is live, the entity is configured, current conditions are rich, hourly forecasts work, daily forecasts include enriched fields, and upcoming milestones are visible without implying they are already shipped.

## Audience

Primary audience:

- Users evaluating whether the integration is useful.
- Maintainers reviewing feature progress.
- The project README or GitLab project page, where a screenshot can summarize the integration quickly.

Secondary audience:

- The developer testing live API behavior in Home Assistant.

## Design Direction

Use the approved **Live Walkthrough Demo** direction.

This is a demo-first card, not a minimal daily weather card. It should still look like something that belongs in Home Assistant, but its main job is to explain the integration's capabilities in one view.

## Scope

In scope:

- A Lovelace card or card stack that can be added to a Home Assistant dashboard.
- Uses the existing weather entity, expected as `weather.the_weather_company`.
- Shows current weather state and key attributes.
- Shows a compact hourly forecast strip.
- Shows a compact enriched daily forecast summary.
- Shows integration coverage and roadmap status.
- Uses real Home Assistant entities and attributes where available.
- Uses clearly labeled placeholders only for future milestones.

Out of scope:

- Backend changes to the integration.
- New weather API endpoints.
- New sensor entities.
- A custom JavaScript Lovelace card.
- A general-purpose dashboard theme.
- HACS packaging for the card.

## Card Layout

The card should use five visual regions.

### 1. Header

Purpose: prove identity and live status.

Content:

- Title: `The Weather Company`.
- Current temperature.
- Current condition phrase.
- Feels-like temperature.
- Configured location label.
- Entity id: `weather.the_weather_company`.
- Live status badge such as `API live`.

The header should be the strongest visual area. It should work well in a screenshot without requiring surrounding dashboard context.

### 2. Current Conditions

Purpose: show that the integration exposes more than temperature.

Fields:

- Humidity.
- Pressure.
- Visibility.
- Wind speed and wind bearing.

### 3. Comfort And Sky

Purpose: showcase the richer current-condition mappings.

Fields:

- Dew point.
- Cloud cover.
- UV index.
- Wind gust.

These fields depend on the richer weather mappings milestone. If that merge request has not landed yet, the card implementation should either omit the unavailable rows or show a neutral unavailable state.

### 4. Integration Coverage

Purpose: explain feature progress during demos.

Rows:

- Current conditions: shipped.
- 2-day hourly forecast: shipped.
- 7-day daily forecast: shipped.
- Weather alerts: planned milestone.
- Optional extra weather entities: planned milestone.

Shipped items should look complete. Planned items should be visually secondary and must not look like live data.

### 5. Forecast Demo

Purpose: show both forecast surfaces in a compact way.

Hourly section:

- Show the next 6 hourly forecast rows.
- Include hour, temperature, and precipitation probability.
- Source is the weather entity's hourly forecast support.

Daily section:

- Show two or three daily rows.
- Include high/low, condition, precipitation probability or amount, and UV where available.
- Include a short label noting that daily rows are enriched with humidity, cloud cover, apparent temperature, precipitation amount, and UV.

## Implementation Approach

Prefer built-in Lovelace cards and widely used dashboard primitives over a custom card:

- Use a vertical stack as the top-level container.
- Use a markdown card for explanatory demo labels only where Home Assistant cannot render the values cleanly.
- Use entity, tile, or custom button-card style cards if the local dashboard already uses them.
- Use weather forecast card support where it cleanly exposes hourly and daily forecast data.
- Avoid custom JavaScript in the repository for this milestone.

If a polished single-card experience requires a third-party Lovelace helper, document that dependency explicitly in the dashboard YAML. Do not make it a runtime dependency of the Home Assistant integration.

## Data Binding

Expected primary entity:

- `weather.the_weather_company`

Current state and attributes should come from that weather entity. The design assumes Home Assistant exposes the relevant weather properties as attributes or card-consumable forecast data.

If Home Assistant does not expose some forecast fields directly to Lovelace cards, the implementation should degrade gracefully:

- Keep the current-condition and coverage sections.
- Use the built-in weather forecast card for forecast presentation.
- Avoid duplicating integration data into template sensors unless a later milestone explicitly approves extra entities.

## Visual Tone

The card should feel like a serious operational Home Assistant dashboard:

- Dense but readable.
- Clear status badges.
- Restrained colors.
- No marketing hero treatment.
- No decorative backgrounds.
- No unrelated illustrations.

Use color only to distinguish live shipped capabilities from planned roadmap items.

## Error And Empty States

The demo card should handle common states:

- Entity unavailable: show a clear unavailable state and keep the integration coverage section visible.
- Missing richer attributes: omit the missing row or show `Unavailable`; do not show fake values.
- Forecast not available: keep current-condition sections and show a short unavailable forecast message.
- Alerts not implemented: show alerts only as a planned milestone, never as active alert data.

## Testing And Verification

Manual verification should cover:

- Card renders on desktop dashboard width.
- Card renders acceptably on a narrow/mobile dashboard width.
- Text does not overlap or overflow.
- Current condition values match the `weather.the_weather_company` entity.
- Hourly forecast section uses hourly data.
- Daily forecast section uses daily data.
- Planned milestones are visually distinct from live data.

If implemented as YAML, validate by loading it into the running Home Assistant test container at `http://localhost:8123`.

## Open Decisions

No product decisions remain open for the first implementation. The approved direction is the Live Walkthrough Demo card.

Implementation may still need to choose exact Lovelace card primitives based on what the local Home Assistant instance supports cleanly.
