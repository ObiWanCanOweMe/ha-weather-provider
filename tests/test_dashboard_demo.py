"""Tests for the demo Lovelace dashboard card."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEMO_CARD_PATH = Path("dashboards/the-weather-company-demo.yaml")
WEATHER_ENTITY_ID = "weather.twc"


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
    assert "weather entity is live as `{{ entity }}`." not in yaml_text


def test_demo_dashboard_shows_integration_release_version() -> None:
    """Demo card should show the integration version from the weather entity."""
    yaml_text = DEMO_CARD_PATH.read_text(encoding="utf-8")

    assert "integration_version = state_attr(entity, 'integration_version')" in yaml_text
    assert "Integration release" in yaml_text
    assert "v{{ integration_version" in yaml_text


def test_demo_dashboard_shows_alert_summary_attributes() -> None:
    """Demo card should show active alert status from weather entity attributes."""
    yaml_text = DEMO_CARD_PATH.read_text(encoding="utf-8")

    assert "alert_count = state_attr(entity, 'alert_count')" in yaml_text
    assert "alert_headlines = state_attr(entity, 'alert_headlines') or []" in yaml_text
    assert "Active Alerts" in yaml_text


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

    assert "| weather alerts | shipped |" in yaml_text
    assert "| current detail and forecast adapter sensors | shipped |" in yaml_text


def test_demo_dashboard_formats_home_assistant_conditions_for_display() -> None:
    """Known Home Assistant weather conditions should display as readable labels."""
    yaml_text = DEMO_CARD_PATH.read_text(encoding="utf-8")

    assert "'partlycloudy': 'Partly Cloudy'" in yaml_text
    assert "condition | replace('_', ' ') | title" not in yaml_text


def test_demo_dashboard_stacks_dense_sections() -> None:
    """Current metrics and forecasts should not use cramped two-column grids."""
    grids = [card for card in _walk_cards(_load_demo_card()) if card.get("type") == "grid"]
    grids_by_title = {grid.get("title"): grid for grid in grids}

    assert grids_by_title["Current Conditions"]["columns"] == 1
    assert grids_by_title["Forecast Demo"]["columns"] == 1


def test_demo_dashboard_does_not_append_units_to_unavailable_values() -> None:
    """Unavailable values should not render with dangling units."""
    yaml_text = DEMO_CARD_PATH.read_text(encoding="utf-8")

    assert "else 'Unavailable' }}%" not in yaml_text
    assert "else 'Unavailable' }}°" not in yaml_text
    assert "else 'Unavailable' }} {{ state_attr" not in yaml_text


def test_demo_dashboard_explains_missing_wind_gust() -> None:
    """Missing gust data should read like a reported calm value, not a broken card."""
    yaml_text = DEMO_CARD_PATH.read_text(encoding="utf-8")

    assert "No gust reported" in yaml_text
    assert (
        "wind_gust ~ ' ' ~ wind_speed_unit if wind_gust is not none else 'Unavailable'"
        not in yaml_text
    )


def test_demo_dashboard_daily_enrichment_uses_bullet_list() -> None:
    """Daily enrichment field list should scan as bullets instead of a sentence."""
    yaml_text = DEMO_CARD_PATH.read_text(encoding="utf-8")

    assert "- High and low temperature" in yaml_text
    assert "- Precipitation chance and amount" in yaml_text
    assert "- Wind" in yaml_text
    assert "- Humidity" in yaml_text
    assert "- Cloud cover" in yaml_text
    assert "- Apparent temperature" in yaml_text
    assert "- UV index" in yaml_text
    assert (
        "high and low temperature, condition, precipitation chance, precipitation amount,"
        not in yaml_text
    )


def test_demo_dashboard_markdown_tables_preserve_row_newlines() -> None:
    """Markdown table cards should keep separator rows on their own lines."""
    cards = _walk_cards(_load_demo_card())
    table_contents = [
        card["content"]
        for card in cards
        if card.get("type") == "markdown" and "| ---" in card.get("content", "")
    ]

    assert table_contents
    assert all("\n| ---" in content for content in table_contents)
