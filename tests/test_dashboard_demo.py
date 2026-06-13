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
