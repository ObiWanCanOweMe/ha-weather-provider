# Demo Dashboard Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a copy-pasteable Home Assistant Lovelace demo dashboard card that showcases the HA Weather Provider integration.

**Architecture:** Add a repository-owned dashboard YAML artifact plus short usage documentation. Use built-in Lovelace cards only (`vertical-stack`, `grid`, `markdown`, and `weather-forecast`) so the demo has no runtime dependency beyond Home Assistant and the existing `weather.the_weather_company` entity.

**Tech Stack:** Home Assistant Lovelace YAML, built-in dashboard cards, pytest, PyYAML from the existing Home Assistant test dependencies.

---

## File Structure

- Create `dashboards/the-weather-company-demo.yaml`
  - Copy-pasteable Lovelace card stack for the demo.
  - Uses `weather.the_weather_company` as the primary entity.
  - Uses markdown templates for current attributes and built-in weather forecast cards for hourly/daily forecast rendering.
- Create `docs/dashboard-demo.md`
  - Explains how to add the demo card to a Home Assistant dashboard.
  - Documents expected entity id and how to adapt it if HA chooses a different id.
  - Documents that planned milestone rows are static labels, not live alert data.
- Create `tests/test_dashboard_demo.py`
  - Validates the YAML file parses.
  - Validates the card references `weather.the_weather_company`.
  - Validates there are hourly and daily forecast cards.
  - Validates planned milestone language stays clearly marked as planned.

## Task 1: Add YAML Validation Tests

**Files:**
- Create: `tests/test_dashboard_demo.py`
- Test: `tests/test_dashboard_demo.py`

- [x] **Step 1: Write failing tests for the dashboard artifact**

Create `tests/test_dashboard_demo.py` with this content:

```python
"""Tests for the demo Lovelace dashboard card."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEMO_CARD_PATH = Path("dashboards/the-weather-company-demo.yaml")
WEATHER_ENTITY_ID = "weather.the_weather_company"


def _load_demo_card() -> dict[str, Any]:
    """Load the demo dashboard YAML."""
    with DEMO_CARD_PATH.open(encoding="utf-8") as file:
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


def test_demo_dashboard_yaml_exists_and_parses() -> None:
    """Demo card YAML should exist and parse as a Lovelace card."""
    card = _load_demo_card()

    assert card["type"] == "vertical-stack"
    assert isinstance(card["cards"], list)
    assert card["cards"]


def test_demo_dashboard_references_weather_company_entity() -> None:
    """Demo card should bind to the expected weather entity id."""
    yaml_text = DEMO_CARD_PATH.read_text(encoding="utf-8")

    assert WEATHER_ENTITY_ID in yaml_text


def test_demo_dashboard_includes_hourly_and_daily_forecast_cards() -> None:
    """Demo card should showcase both hourly and daily forecast support."""
    cards = _walk_cards(_load_demo_card())
    forecast_cards = [
        card
        for card in cards
        if card.get("type") == "weather-forecast"
        and card.get("entity") == WEATHER_ENTITY_ID
    ]

    assert any(card.get("forecast_type") == "hourly" for card in forecast_cards)
    assert any(card.get("forecast_type") == "daily" for card in forecast_cards)


def test_demo_dashboard_marks_future_features_as_planned() -> None:
    """Roadmap features must not look like live alert or sensor data."""
    yaml_text = DEMO_CARD_PATH.read_text(encoding="utf-8").lower()

    assert "weather alerts" in yaml_text
    assert "optional extra weather entities" in yaml_text
    assert "planned" in yaml_text
```

- [x] **Step 2: Run the new tests and verify they fail because the file is missing**

Run:

```bash
.venv/bin/python -m pytest tests/test_dashboard_demo.py -q
```

Expected:

```text
FAILED tests/test_dashboard_demo.py::test_demo_dashboard_yaml_exists_and_parses
```

The failure should be `FileNotFoundError` for `dashboards/the-weather-company-demo.yaml`.

- [x] **Step 3: Commit the failing tests**

Run:

```bash
git add tests/test_dashboard_demo.py
git commit -m "test: add demo dashboard validation"
```

## Task 2: Add The Demo Lovelace Card

**Files:**
- Create: `dashboards/the-weather-company-demo.yaml`
- Test: `tests/test_dashboard_demo.py`

- [x] **Step 1: Create the dashboard YAML**

Create `dashboards/the-weather-company-demo.yaml` with this content:

```yaml
type: vertical-stack
cards:
  - type: markdown
    title: The Weather Company
    content: >-
      {% set entity = 'weather.the_weather_company' %}
      {% set condition = states(entity) %}
      {% set temp = state_attr(entity, 'temperature') %}
      {% set apparent = state_attr(entity, 'apparent_temperature') %}
      {% set attribution = state_attr(entity, 'attribution') %}

      # {{ temp if temp is not none else '--' }}° {{ condition | replace('_', ' ') | title }}

      **The Weather Company** weather entity is live as `{{ entity }}`.

      {% if apparent is not none %}
      Feels like **{{ apparent }}°**.
      {% endif %}

      {% if attribution %}
      {{ attribution }}
      {% endif %}

      <ha-alert alert-type="success">API live · Current conditions · 2-day hourly · 7-day daily</ha-alert>

  - type: grid
    title: Current Conditions
    columns: 2
    square: false
    cards:
      - type: markdown
        content: >-
          {% set entity = 'weather.the_weather_company' %}
          ### Atmosphere

          | Metric | Value |
          | --- | ---: |
          | Humidity | {{ state_attr(entity, 'humidity') if state_attr(entity, 'humidity') is not none else 'Unavailable' }}% |
          | Pressure | {{ state_attr(entity, 'pressure') if state_attr(entity, 'pressure') is not none else 'Unavailable' }} {{ state_attr(entity, 'pressure_unit') or '' }} |
          | Visibility | {{ state_attr(entity, 'visibility') if state_attr(entity, 'visibility') is not none else 'Unavailable' }} {{ state_attr(entity, 'visibility_unit') or '' }} |
          | Wind | {{ state_attr(entity, 'wind_speed') if state_attr(entity, 'wind_speed') is not none else 'Unavailable' }} {{ state_attr(entity, 'wind_speed_unit') or '' }} · {{ state_attr(entity, 'wind_bearing') if state_attr(entity, 'wind_bearing') is not none else 'Unavailable' }} |

      - type: markdown
        content: >-
          {% set entity = 'weather.the_weather_company' %}
          ### Comfort & Sky

          | Metric | Value |
          | --- | ---: |
          | Dew point | {{ state_attr(entity, 'dew_point') if state_attr(entity, 'dew_point') is not none else 'Unavailable' }}° |
          | Cloud cover | {{ state_attr(entity, 'cloud_coverage') if state_attr(entity, 'cloud_coverage') is not none else 'Unavailable' }}% |
          | UV index | {{ state_attr(entity, 'uv_index') if state_attr(entity, 'uv_index') is not none else 'Unavailable' }} |
          | Wind gust | {{ state_attr(entity, 'wind_gust_speed') if state_attr(entity, 'wind_gust_speed') is not none else 'Unavailable' }} {{ state_attr(entity, 'wind_speed_unit') or '' }} |

  - type: markdown
    title: Integration Coverage
    content: >-
      | Capability | Status |
      | --- | --- |
      | Current conditions | Shipped |
      | 2-day hourly forecast | Shipped |
      | 7-day daily forecast | Shipped |
      | Weather alerts | Planned milestone |
      | Optional extra weather entities | Planned milestone |

  - type: grid
    title: Forecast Demo
    columns: 2
    square: false
    cards:
      - type: weather-forecast
        entity: weather.the_weather_company
        name: Hourly Forecast
        forecast_type: hourly
        show_current: false
        show_forecast: true

      - type: weather-forecast
        entity: weather.the_weather_company
        name: Daily Forecast
        forecast_type: daily
        show_current: false
        show_forecast: true

  - type: markdown
    title: Daily Enrichment
    content: >-
      Daily forecast rows are enriched by the integration where Home Assistant supports the fields:
      high and low temperature, condition, precipitation chance, precipitation amount,
      wind, humidity, cloud cover, apparent temperature, and UV index.

      Planned milestones are intentionally shown as roadmap labels only.
```

- [x] **Step 2: Run the dashboard tests and verify they pass**

Run:

```bash
.venv/bin/python -m pytest tests/test_dashboard_demo.py -q
```

Expected:

```text
4 passed
```

- [x] **Step 3: Commit the dashboard YAML**

Run:

```bash
git add dashboards/the-weather-company-demo.yaml
git commit -m "docs: add Weather Company demo dashboard card"
```

## Task 3: Add Usage Documentation

**Files:**
- Create: `docs/dashboard-demo.md`
- Modify: `dashboards/the-weather-company-demo.yaml`
- Test: `tests/test_dashboard_demo.py`

- [x] **Step 1: Create usage documentation**

Create `docs/dashboard-demo.md` with this content:

```markdown
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
```

- [x] **Step 2: Add a documentation link comment to the YAML**

At the top of `dashboards/the-weather-company-demo.yaml`, insert:

```yaml
# Demo card usage: docs/dashboard-demo.md
```

The first lines of the YAML should become:

```yaml
# Demo card usage: docs/dashboard-demo.md
type: vertical-stack
cards:
```

- [x] **Step 3: Run dashboard tests again**

Run:

```bash
.venv/bin/python -m pytest tests/test_dashboard_demo.py -q
```

Expected:

```text
4 passed
```

- [x] **Step 4: Commit the docs**

Run:

```bash
git add docs/dashboard-demo.md dashboards/the-weather-company-demo.yaml
git commit -m "docs: document demo dashboard card"
```

## Task 4: Runtime Verification In Home Assistant

**Files:**
- Read: `dashboards/the-weather-company-demo.yaml`
- Read: `docs/testing.md`

- [x] **Step 1: Confirm the HA container is running**

Run:

```bash
docker ps --filter name=ha-weather-provider-test --format '{{.Names}} {{.Status}} {{.Ports}}'
```

Expected:

```text
ha-weather-provider-test Up ... 0.0.0.0:8123->8123/tcp
```

If it is not running, start it using the repo's documented HA test container workflow before continuing.

- [x] **Step 2: Confirm the weather entity id**

Open Home Assistant at:

```text
http://localhost:8123
```

Go to **Developer Tools > States** and search for:

```text
weather.the_weather_company
```

Expected:

- The entity exists.
- It has current weather state.
- It has attributes for at least temperature, humidity, pressure, wind, visibility, UV, and forecast support.

- [ ] **Step 3: Add the manual card**

In Home Assistant:

1. Open the target dashboard.
2. Select **Edit dashboard**.
3. Add a **Manual** card.
4. Paste the contents of `dashboards/the-weather-company-demo.yaml`.
5. Save.

Expected:

- Header renders with current temperature and condition.
- Current Conditions section renders two markdown cards.
- Integration Coverage table clearly marks alerts and optional entities as planned.
- Forecast Demo renders hourly and daily weather forecast cards.

- [ ] **Step 4: Check responsive layout**

Use browser responsive tools or resize the browser:

- Desktop width: all sections should be readable with no overlap.
- Narrow width: grid cards should wrap or stack without text clipping.

- [x] **Step 5: Capture any runtime incompatibility**

If a built-in card option is unsupported by the installed Home Assistant version, adjust `dashboards/the-weather-company-demo.yaml` to the smallest compatible built-in-card alternative and rerun:

```bash
.venv/bin/python -m pytest tests/test_dashboard_demo.py -q
```

Then commit the compatibility fix:

```bash
git add dashboards/the-weather-company-demo.yaml tests/test_dashboard_demo.py
git commit -m "fix: make demo dashboard compatible with HA card schema"
```

Runtime note: automated verification confirmed the HA container was running, the
`weather.the_weather_company` entity existed, the expected current attributes
were present through the HA REST API, and the YAML parsed with hourly/daily
forecast cards and preserved markdown table newlines. Browser access was not
available in this Codex session, so the manual paste/render and responsive
layout checks remain manual follow-up steps.

## Task 5: Full Verification And MR

**Files:**
- Verify all changed files.

- [x] **Step 1: Run focused dashboard tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_dashboard_demo.py -q
```

Expected:

```text
4 passed
```

- [x] **Step 2: Run the full test suite**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected:

```text
48 passed
```

The exact count may be higher if new tests have been added after this plan; there must be zero failures.

- [x] **Step 3: Run the harness project check**

Run:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .
```

Expected:

```text
... 48 passed ...
```

The exact count may be higher if new tests have been added after this plan; there must be zero failures.

- [x] **Step 4: Check git status**

Run:

```bash
git status --short --branch
```

Expected:

```text
## demo-dashboard-card...origin/demo-dashboard-card
```

No uncommitted files should remain.

- [ ] **Step 5: Push and open a GitLab MR**

Run:

```bash
git push -u origin demo-dashboard-card
glab mr create \
  --source-branch demo-dashboard-card \
  --target-branch master \
  --title "Add Weather Company demo dashboard card" \
  --description $'## Summary\n- add a copy-pasteable Lovelace demo card for the Weather Company integration\n- document dashboard usage and expected entity id\n- validate the dashboard YAML with tests\n\n## Verification\n- .venv/bin/python -m pytest tests/test_dashboard_demo.py -q\n- .venv/bin/python -m pytest -q\n- obi-dev-harness project-check .\n- manual Home Assistant dashboard render check' \
  --yes
```

Expected:

- GitLab returns a merge request URL.
- MR targets `master`.
