# TWC Weather Card Gallery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase 1 repository artifacts for a Home Assistant dashboard gallery that maps the SmartHomeScene top 10 weather cards to The Weather Company data.

**Architecture:** Add a repo-only dashboard YAML, setup documentation, compatibility catalog, and optional template-helper examples without installing or bundling third-party cards. Tests validate that the gallery parses, references `weather.twc`, includes all ten article cards, documents dependency status, and calls out non-TWC dependencies.

**Tech Stack:** Home Assistant Lovelace YAML, Markdown docs, Python pytest, PyYAML.

---

## File Structure

- `dashboards/the-weather-company-card-gallery.yaml`: new Lovelace dashboard/card stack for the card gallery.
- `docs/weather-card-gallery.md`: user-facing setup and compatibility guide.
- `docs/examples/twc-weather-card-gallery-template-sensors.yaml`: optional Home Assistant template helpers for cards that expect sensor entities.
- `tests/test_weather_card_gallery.py`: repository tests for YAML/docs/catalog coverage.

This first implementation slice is Phase 1 only. Do not install HACS, download third-party card JavaScript, change the integration backend, or apply the dashboard to the running HA container in this branch.

### Task 1: Gallery Artifact Tests

**Files:**
- Create: `tests/test_weather_card_gallery.py`
- Read: `docs/superpowers/specs/2026-06-14-twc-weather-card-gallery-design.md`

- [x] **Step 1: Write failing gallery tests**

Create `tests/test_weather_card_gallery.py`:

```python
"""Tests for the TWC weather card gallery dashboard artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

GALLERY_DASHBOARD_PATH = Path("dashboards/the-weather-company-card-gallery.yaml")
GALLERY_DOC_PATH = Path("docs/weather-card-gallery.md")
TEMPLATE_SENSOR_PATH = Path("docs/examples/twc-weather-card-gallery-template-sensors.yaml")
WEATHER_ENTITY_ID = "weather.twc"

ARTICLE_CARD_NAMES = (
    "Home Assistant Weather Forecast Card",
    "Simple Weather Card",
    "Hourly Weather Card",
    "Animated Weather Card",
    "Weather Radar Card",
    "Clock Weather Card",
    "Meteoalarm Card",
    "Lovelace Horizon Card",
    "Weather Conditions Card",
    "Platinum Weather Card",
)

REQUIRED_STATUSES = (
    "Live",
    "Requires HACS card",
    "Requires adapter entities",
    "Requires non-TWC source",
    "Research needed",
)


def _load_gallery_dashboard() -> dict[str, Any]:
    """Load the gallery Lovelace YAML."""
    with GALLERY_DASHBOARD_PATH.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)

    assert isinstance(data, dict)
    return data


def _walk_cards(card: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every nested Lovelace card dictionary."""
    cards = [card]
    for child in card.get("cards", []):
        if isinstance(child, dict):
            cards.extend(_walk_cards(child))
    return cards


def test_weather_card_gallery_yaml_exists_and_parses() -> None:
    """Gallery dashboard YAML should exist and parse as a Lovelace stack."""
    card = _load_gallery_dashboard()

    assert card["type"] == "vertical-stack"
    assert isinstance(card["cards"], list)
    assert card["cards"]


def test_weather_card_gallery_references_twc_entity() -> None:
    """Gallery should bind examples to the expected TWC weather entity."""
    yaml_text = GALLERY_DASHBOARD_PATH.read_text(encoding="utf-8")

    assert WEATHER_ENTITY_ID in yaml_text
    assert "weather.forecast_home" not in yaml_text
    assert "weather.forecast_home_hourly" not in yaml_text


def test_weather_card_gallery_represents_all_article_cards() -> None:
    """All ten article cards should appear in the gallery dashboard."""
    yaml_text = GALLERY_DASHBOARD_PATH.read_text(encoding="utf-8")
    docs_text = GALLERY_DOC_PATH.read_text(encoding="utf-8")

    for card_name in ARTICLE_CARD_NAMES:
        assert card_name in yaml_text
        assert card_name in docs_text


def test_weather_card_gallery_documents_dependency_statuses() -> None:
    """Gallery docs should include each supported dependency status."""
    docs_text = GALLERY_DOC_PATH.read_text(encoding="utf-8")

    for status in REQUIRED_STATUSES:
        assert status in docs_text


def test_weather_card_gallery_includes_custom_card_examples() -> None:
    """Gallery should include concrete custom-card YAML examples."""
    cards = _walk_cards(_load_gallery_dashboard())
    card_types = {card.get("type") for card in cards}

    assert "weather-forecast" in card_types
    assert "custom:simple-weather-card" in card_types
    assert "custom:hourly-weather" in card_types
    assert "custom:clock-weather-card" in card_types
    assert "custom:weather-radar-card" in card_types
    assert "custom:meteoalarm-card" in card_types
    assert "custom:ha-card-weather-conditions" in card_types
    assert "custom:platinum-weather-card" in card_types


def test_weather_card_gallery_calls_out_non_twc_dependencies() -> None:
    """Radar and sun cards should not be presented as fully TWC-backed."""
    yaml_text = GALLERY_DASHBOARD_PATH.read_text(encoding="utf-8")
    docs_text = GALLERY_DOC_PATH.read_text(encoding="utf-8")

    assert "sun.sun" in yaml_text
    assert "RainViewer" in yaml_text
    assert "not TWC-backed" in docs_text
    assert "Requires non-TWC source" in docs_text


def test_weather_card_gallery_template_sensor_examples_parse() -> None:
    """Adapter helper YAML should parse and expose predictable entity names."""
    with TEMPLATE_SENSOR_PATH.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)

    assert isinstance(data, dict)
    yaml_text = TEMPLATE_SENSOR_PATH.read_text(encoding="utf-8")
    assert "sensor.twc_demo_condition" in yaml_text
    assert "twc_demo_temperature" in yaml_text
    assert "twc_demo_feels_like" in yaml_text
    assert "twc_demo_wind_gust" in yaml_text
    assert WEATHER_ENTITY_ID in yaml_text


def test_weather_card_gallery_docs_explain_setup_boundaries() -> None:
    """Docs should explain Phase 1 repo artifacts versus live HACS setup."""
    docs_text = GALLERY_DOC_PATH.read_text(encoding="utf-8")

    assert "Phase 1" in docs_text
    assert "Phase 2" in docs_text
    assert "HACS" in docs_text
    assert "does not bundle third-party JavaScript" in docs_text
    assert "replace every `weather.twc` reference" in docs_text
```

- [x] **Step 2: Run tests to verify failure**

Run:

```bash
PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_weather_card_gallery.py -q
```

Expected: FAIL because `dashboards/the-weather-company-card-gallery.yaml`, `docs/weather-card-gallery.md`, and `docs/examples/twc-weather-card-gallery-template-sensors.yaml` do not exist yet.

- [x] **Step 3: Commit failing tests**

Run:

```bash
git add tests/test_weather_card_gallery.py
git commit -m "Add weather card gallery artifact tests"
```

Expected: commit succeeds with only the new test file staged.

### Task 2: Dashboard YAML Gallery

**Files:**
- Create: `dashboards/the-weather-company-card-gallery.yaml`
- Test: `tests/test_weather_card_gallery.py`

- [x] **Step 1: Add the gallery dashboard YAML**

Create `dashboards/the-weather-company-card-gallery.yaml`:

```yaml
# Demo docs: docs/weather-card-gallery.md
type: vertical-stack
cards:
  - type: markdown
    title: TWC Weather Card Gallery
    content: |-
      {% set entity = 'weather.twc' %}
      {% set temp = state_attr(entity, 'temperature') %}
      {% set apparent = state_attr(entity, 'apparent_temperature') %}
      {% set version = state_attr(entity, 'integration_version') %}
      {% set alert_count = state_attr(entity, 'alert_count') %}

      # The Weather Company Card Gallery

      **Entity:** `{{ entity }}`

      **Current:** {{ states(entity) | replace('-', ' ') | title }} · {{ temp if temp is not none else 'Unavailable' }}°

      {% if apparent is not none %}
      **Feels like:** {{ apparent }}°
      {% endif %}

      **Active alerts:** {{ alert_count if alert_count is not none else 'Unavailable' }}

      **Integration release:** v{{ version if version is not none else 'unknown' }}

      This gallery maps popular Home Assistant weather cards to TWC data where possible.

  - type: markdown
    title: Compatibility Summary
    content: |-
      | Card | Status | Primary Source |
      | --- | --- | --- |
      | Home Assistant Weather Forecast Card | Live | `weather.twc` |
      | Simple Weather Card | Requires HACS card | `weather.twc` |
      | Hourly Weather Card | Requires HACS card | `weather.twc` hourly forecast |
      | Animated Weather Card | Requires adapter entities | `sensor.twc_demo_*` |
      | Weather Radar Card | Requires non-TWC source | RainViewer radar tiles |
      | Clock Weather Card | Requires HACS card | `weather.twc`, `sun.sun` |
      | Meteoalarm Card | Research needed | TWC alert summary |
      | Lovelace Horizon Card | Requires non-TWC source | `sun.sun` |
      | Weather Conditions Card | Requires adapter entities | `sensor.twc_demo_*` |
      | Platinum Weather Card | Requires adapter entities | `weather.twc`, `sensor.twc_demo_*` |

  - type: markdown
    title: Home Assistant Weather Forecast Card
    content: |-
      Status: **Live**

      Built-in Home Assistant card using `weather.twc`.

  - type: weather-forecast
    entity: weather.twc
    name: Home Assistant Weather Forecast Card
    forecast_type: daily
    show_current: true
    show_forecast: true

  - type: markdown
    title: Simple Weather Card
    content: |-
      Status: **Requires HACS card**

      Uses `weather.twc` directly once `custom:simple-weather-card` is installed.

  - type: custom:simple-weather-card
    entity: weather.twc
    name: The Weather Company
    primary_info:
      - wind_bearing
      - humidity
    secondary_info:
      - precipitation
      - precipitation_probability

  - type: markdown
    title: Hourly Weather Card
    content: |-
      Status: **Requires HACS card**

      Uses the hourly forecast exposed by `weather.twc`.

  - type: custom:hourly-weather
    entity: weather.twc
    icons: true
    show_precipitation_amounts: true
    show_wind: barb
    num_segments: "14"

  - type: markdown
    title: Clock Weather Card
    content: |-
      Status: **Requires HACS card**

      Uses `weather.twc` for forecast data and `sun.sun` for sun context.

  - type: custom:clock-weather-card
    entity: weather.twc
    sun_entity: sun.sun
    weather_icon_type: line
    animated_icon: true
    forecast_days: 5
    locale: en-US
    time_format: 12
    hide_today_section: false
    hide_forecast_section: false

  - type: markdown
    title: Animated Weather Card
    content: |-
      Status: **Requires adapter entities**

      This card family expects many sensor-style inputs. See `docs/examples/twc-weather-card-gallery-template-sensors.yaml`.

  - type: custom:bom-weather-card
    title: Animated Weather Card
    entity_current_conditions: sensor.twc_demo_condition
    entity_temperature: sensor.twc_demo_temperature
    entity_apparent_temp: sensor.twc_demo_feels_like
    entity_wind_bearing: sensor.twc_demo_wind_bearing
    entity_wind_speed: sensor.twc_demo_wind_speed
    entity_wind_gust: sensor.twc_demo_wind_gust

  - type: markdown
    title: Platinum Weather Card
    content: |-
      Status: **Requires adapter entities**

      Uses `weather.twc` where supported and adapter sensors for detailed slots.

  - type: custom:platinum-weather-card
    card_config_version: 8
    entity: weather.twc
    entity_forecast_icon: weather.twc
    entity_summary: sensor.twc_demo_condition
    entity_temperature: sensor.twc_demo_temperature
    option_show_overview_decimals: true
    option_show_overview_separator: false
    overview_layout: complete
    section_order:
      - overview
      - extended
      - slots
      - daily_forecast
    show_section_overview: true
    text_card_title: Weather
    text_card_title_2: TWC

  - type: markdown
    title: Weather Conditions Card
    content: |-
      Status: **Requires adapter entities**

      Advanced weather-station style card. TWC can provide core weather values; pollen, air quality, and meteogram data are not currently exposed by this integration.

  - type: custom:ha-card-weather-conditions
    name: Weather Conditions Card
    language: en
    animation: true
    weather:
      icons_model: climacell
      current:
        sun: sun.sun
        current_conditions: sensor.twc_demo_condition
        temperature: sensor.twc_demo_temperature
        feels_like: sensor.twc_demo_feels_like
        humidity: sensor.twc_demo_humidity
        pressure: sensor.twc_demo_pressure
        wind_speed: sensor.twc_demo_wind_speed

  - type: markdown
    title: Meteoalarm Card
    content: |-
      Status: **Research needed**

      The article card targets alert integrations such as Meteoalarm. TWC alert headline data is available, but direct card compatibility needs live testing.

  - type: custom:meteoalarm-card
    entities:
      - entity: sensor.twc_alert_count
    integration: meteoalarm
    override_headline: true

  - type: markdown
    title: Lovelace Horizon Card
    content: |-
      Status: **Requires non-TWC source**

      Uses Home Assistant's `sun.sun` integration. Useful weather-dashboard context, but not TWC-backed.

  - type: custom:sun-card
    darkMode: true
    showAzimuth: true
    showElevation: true

  - type: markdown
    title: Weather Radar Card
    content: |-
      Status: **Requires non-TWC source**

      The Weather Radar Card uses RainViewer map tiles. This is useful context but not TWC-backed.

  - type: custom:weather-radar-card
    frame_count: 10
    center_latitude: 33.931
    center_longitude: -84.4677
    marker_latitude: 33.931
    marker_longitude: -84.4677
    show_marker: true
    show_range: true
    show_zoom: true
    show_recenter: true
    show_playback: true
    zoom_level: 8
```

- [x] **Step 2: Run gallery tests and verify dashboard-related failures shrink**

Run:

```bash
PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_weather_card_gallery.py -q
```

Expected: tests still FAIL because docs and template sensors are not present, but dashboard parse and card-type assertions should pass.

- [x] **Step 3: Commit dashboard YAML**

Run:

```bash
git add dashboards/the-weather-company-card-gallery.yaml
git commit -m "Add TWC weather card gallery dashboard"
```

Expected: commit succeeds with only the gallery dashboard file staged.

### Task 3: Template Helper Examples

**Files:**
- Create: `docs/examples/twc-weather-card-gallery-template-sensors.yaml`
- Test: `tests/test_weather_card_gallery.py`

- [x] **Step 1: Add template helper YAML**

Create `docs/examples/twc-weather-card-gallery-template-sensors.yaml`:

```yaml
# Optional Home Assistant template helpers for the TWC weather card gallery.
# Add these to configuration.yaml or split template YAML if a custom card expects sensor entities.
# Expected entity ids include sensor.twc_demo_condition, sensor.twc_demo_temperature,
# sensor.twc_demo_feels_like, sensor.twc_demo_wind_speed, and sensor.twc_demo_wind_gust.
template:
  - sensor:
      - name: TWC Demo Condition
        unique_id: twc_demo_condition
        state: "{{ states('weather.twc') }}"

      - name: TWC Demo Temperature
        unique_id: twc_demo_temperature
        state: "{{ state_attr('weather.twc', 'temperature') }}"

      - name: TWC Demo Feels Like
        unique_id: twc_demo_feels_like
        state: "{{ state_attr('weather.twc', 'apparent_temperature') }}"

      - name: TWC Demo Humidity
        unique_id: twc_demo_humidity
        state: "{{ state_attr('weather.twc', 'humidity') }}"

      - name: TWC Demo Pressure
        unique_id: twc_demo_pressure
        state: "{{ state_attr('weather.twc', 'pressure') }}"

      - name: TWC Demo Wind Speed
        unique_id: twc_demo_wind_speed
        state: "{{ state_attr('weather.twc', 'wind_speed') }}"

      - name: TWC Demo Wind Bearing
        unique_id: twc_demo_wind_bearing
        state: "{{ state_attr('weather.twc', 'wind_bearing') }}"

      - name: TWC Demo Wind Gust
        unique_id: twc_demo_wind_gust
        state: "{{ state_attr('weather.twc', 'wind_gust_speed') }}"

      - name: TWC Demo Alert Summary
        unique_id: twc_demo_alert_summary
        state: >-
          {% set count = state_attr('weather.twc', 'alert_count') | int(0) %}
          {{ count }} active alert{{ '' if count == 1 else 's' }}
```

- [x] **Step 2: Run gallery tests and verify remaining failures are docs-only**

Run:

```bash
PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_weather_card_gallery.py -q
```

Expected: tests still FAIL only because `docs/weather-card-gallery.md` does not exist.

- [x] **Step 3: Commit template helpers**

Run:

```bash
git add docs/examples/twc-weather-card-gallery-template-sensors.yaml
git commit -m "Add TWC weather card gallery template helpers"
```

Expected: commit succeeds with only the helper YAML staged.

### Task 4: Gallery Documentation

**Files:**
- Create: `docs/weather-card-gallery.md`
- Test: `tests/test_weather_card_gallery.py`

- [x] **Step 1: Add the setup and compatibility guide**

Create `docs/weather-card-gallery.md`:

```markdown
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
```

- [x] **Step 2: Run gallery tests and verify they pass**

Run:

```bash
PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_weather_card_gallery.py -q
```

Expected: all `tests/test_weather_card_gallery.py` tests pass.

- [x] **Step 3: Commit gallery documentation**

Run:

```bash
git add docs/weather-card-gallery.md
git commit -m "Document TWC weather card gallery setup"
```

Expected: commit succeeds with only the docs file staged.

### Task 5: Full Verification

**Files:**
- Modify: `docs/superpowers/plans/2026-06-14-twc-weather-card-gallery.md`

- [x] **Step 1: Run the full test suite**

Run:

```bash
PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest
```

Expected: all tests pass.

- [x] **Step 2: Run Ruff**

Run:

```bash
.worktrees/demo-dashboard-card/.venv/bin/ruff check .
```

Expected: `All checks passed!`

- [x] **Step 3: Run Obi project checks**

Run:

```bash
PATH=".worktrees/demo-dashboard-card/.venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .
```

Expected: compile/json checks pass and pytest reports all tests passing.

- [x] **Step 4: Review git status**

Run:

```bash
git status --short --branch
```

Expected: only the unrelated untracked `docs/Weather Company Data  | API Common Usage Guide.pdf` remains outside the committed work.

- [x] **Step 5: Commit plan checklist updates**

After checking completed steps in this plan, run:

```bash
git add docs/superpowers/plans/2026-06-14-twc-weather-card-gallery.md
git commit -m "Track weather card gallery implementation plan"
```

Expected: commit succeeds with only the updated plan staged.

### Task 6: Integration Workflow

**Files:**
- No file edits unless MR description changes are needed.

- [x] **Step 1: Push the branch**

Run:

```bash
git push
```

Expected: local branch pushes cleanly.

- [x] **Step 2: Open a GitLab MR if working on a feature branch**

If the work was implemented on a feature branch, open an MR into `master`:

```bash
glab mr create --source-branch twc-weather-card-gallery --target-branch master --title "Add TWC weather card gallery" --description "## Summary

- Add a TWC weather card gallery dashboard.
- Document the SmartHomeScene top 10 card compatibility mapping.
- Add optional template helper examples for cards that expect sensor entities.

## Verification

- \`PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest\`
- \`.worktrees/demo-dashboard-card/.venv/bin/ruff check .\`
- \`PATH=\".worktrees/demo-dashboard-card/.venv/bin:\$PATH\" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .\`" --remove-source-branch --yes
```

Expected: GitLab returns an MR URL.

- [ ] **Step 3: If working directly on `master`, report local commits**

If the work was implemented directly on `master`, do not create an MR from `master` to `master`. Report the local commits and ask whether to push `master`.
