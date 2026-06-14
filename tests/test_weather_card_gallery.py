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
