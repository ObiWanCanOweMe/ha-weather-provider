"""Tests for the TWC weather card gallery dashboard artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

GALLERY_DASHBOARD_PATH = Path("dashboards/the-weather-company-card-gallery.yaml")
SIMPLE_WEATHER_COMPAT_RESOURCE_PATH = Path(
    "dashboards/resources/twc-simple-weather-card-compat.js"
)
GALLERY_DOC_PATH = Path("docs/weather-card-gallery.md")
GALLERY_DEPENDENCY_DOC_PATH = Path("docs/weather-card-gallery-dependencies.md")
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
    "Installed via HACS",
    "Requires HACS card",
    "Requires adapter entities",
    "Requires non-TWC source",
    "Research needed",
    "Adapter needed",
)


def _load_gallery_dashboard() -> dict[str, Any]:
    """Load the gallery Lovelace YAML."""
    with GALLERY_DASHBOARD_PATH.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)

    assert isinstance(data, dict)
    return data


def _gallery_sections() -> list[dict[str, Any]]:
    """Return the gallery view sections."""
    sections = _load_gallery_dashboard()["sections"]

    assert isinstance(sections, list)
    assert all(isinstance(section, dict) for section in sections)
    return sections


def _section_cards() -> list[dict[str, Any]]:
    """Return every top-level card from every gallery section."""
    cards: list[dict[str, Any]] = []
    for section in _gallery_sections():
        section_cards = section["cards"]
        assert isinstance(section_cards, list)
        cards.extend(card for card in section_cards if isinstance(card, dict))
    return cards


def _walk_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return every nested Lovelace card dictionary."""
    walked: list[dict[str, Any]] = []
    for card in cards:
        walked.append(card)
        child_cards = card.get("cards", [])
        if isinstance(child_cards, list):
            walked.extend(
                _walk_cards([child for child in child_cards if isinstance(child, dict)])
            )
    return walked


def test_weather_card_gallery_yaml_exists_and_parses() -> None:
    """Gallery dashboard YAML should parse as a Home Assistant Sections view."""
    dashboard = _load_gallery_dashboard()
    sections = _gallery_sections()

    assert dashboard["title"] == "TWC Card Gallery"
    assert dashboard["path"] == "default_view"
    assert dashboard["type"] == "sections"
    assert dashboard["max_columns"] == 3
    assert "cards" not in dashboard
    assert sections
    assert all(section["type"] == "grid" for section in sections)
    assert sum(len(section["cards"]) for section in sections) == 22
    assert all(card.get("type") != "vertical-stack" for card in _section_cards())


def test_weather_card_gallery_groups_descriptors_with_demo_cards() -> None:
    """Every card-specific section should keep its descriptor beside its demo card."""
    card_sections = _gallery_sections()[1:]

    for section in card_sections:
        cards = section["cards"]
        assert len(cards) == 2
        assert cards[0]["type"] == "markdown"
        assert cards[0]["title"] == section["title"]
        assert cards[1]["type"] != "markdown"


def test_weather_card_gallery_references_twc_entity() -> None:
    """Gallery should bind examples to the expected TWC weather entity."""
    yaml_text = GALLERY_DASHBOARD_PATH.read_text(encoding="utf-8")

    assert WEATHER_ENTITY_ID in yaml_text
    assert "twc_demo" not in yaml_text
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
    cards = _walk_cards(_section_cards())
    card_types = {card.get("type") for card in cards}

    assert "weather-forecast" in card_types
    assert "custom:simple-weather-card" in card_types
    assert "custom:hourly-weather" in card_types
    assert "custom:clock-weather-card" in card_types
    assert "custom:weather-radar-card" in card_types
    assert "custom:horizon-card" in card_types
    assert "custom:sun-card" not in card_types
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


def test_meteoalarm_section_does_not_instantiate_invalid_twc_alert_config() -> None:
    """Meteoalarm card should not be configured with unsupported TWC alert sensors."""
    cards = _walk_cards(_section_cards())
    card_types = {card.get("type") for card in cards}
    yaml_text = GALLERY_DASHBOARD_PATH.read_text(encoding="utf-8")

    assert "custom:meteoalarm-card" not in card_types
    assert "sensor.twc_alert_count" in yaml_text
    assert yaml_text.count("sensor.twc_alert_count") == 1


def test_weather_conditions_card_uses_supported_present_schema() -> None:
    """Weather Conditions Card config should use its documented present schema."""
    cards = _walk_cards(_section_cards())
    weather_conditions_card = next(
        card for card in cards if card.get("type") == "custom:ha-card-weather-conditions"
    )

    weather_config = weather_conditions_card["weather"]
    assert "current" not in weather_config
    assert weather_conditions_card.get("animation") is None
    assert weather_config["animation"] is True
    assert weather_config["sun"] == "sun.sun"
    assert "sun" not in weather_config["present"]
    assert weather_config["present"]["condition"] == "sensor.twc_condition_phrase"
    assert (
        weather_config["present"]["temperature_feelslike"]
        == "sensor.twc_feels_like_temperature"
    )


def test_animated_weather_card_uses_complete_minimal_schema() -> None:
    """Animated Weather Card config should avoid the card's provider-specific defaults."""
    cards = _walk_cards(_section_cards())
    animated_card = next(card for card in cards if card.get("type") == "custom:bom-weather-card")

    assert animated_card["entity_current_conditions"] == "sensor.twc_condition_phrase"
    assert animated_card["entity_current_text"] == "sensor.twc_condition_phrase"
    assert animated_card["entity_temperature"] == "sensor.twc_temperature"
    assert animated_card["entity_apparent_temp"] == "sensor.twc_feels_like_temperature"
    assert animated_card["entity_humidity"] == "sensor.twc_humidity"
    assert animated_card["entity_pressure"] == "sensor.twc_pressure"
    assert animated_card["entity_wind_bearing"] == "sensor.twc_wind_bearing"
    assert animated_card["entity_wind_speed"] == "sensor.twc_wind_speed"
    assert animated_card["entity_wind_gust"] == "sensor.twc_wind_gust"

    for index in range(1, 6):
        prefix = f"sensor.twc_daily_forecast_day_{index}"
        assert animated_card[f"entity_forecast_icon_{index}"] == f"{prefix}_condition"
        assert (
            animated_card[f"entity_forecast_high_temp_{index}"]
            == f"{prefix}_high"
        )
        assert animated_card[f"entity_forecast_low_temp_{index}"] == f"{prefix}_low"
        assert animated_card[f"entity_pop_{index}"] == f"{prefix}_precip_probability"
        assert animated_card[f"entity_pos_{index}"] == f"{prefix}_precip_amount"
        assert animated_card[f"entity_summary_{index}"] == f"{prefix}_summary"

    assert animated_card["slot_l1"] == "wind"
    assert animated_card["slot_l2"] == "humidity"
    assert animated_card["slot_l3"] == "pressure"
    assert all(animated_card[f"slot_l{index}"] == "empty" for index in range(4, 6))
    assert all(animated_card[f"slot_r{index}"] == "empty" for index in range(1, 6))


def test_clock_weather_card_uses_current_forecast_rows_option() -> None:
    """Clock Weather Card config should use the current v2 forecast option name."""
    cards = _walk_cards(_section_cards())
    clock_card = next(card for card in cards if card.get("type") == "custom:clock-weather-card")

    assert "forecast_days" not in clock_card
    assert clock_card["forecast_rows"] == 5


def test_weather_card_gallery_docs_explain_setup_boundaries() -> None:
    """Docs should explain Phase 1 repo artifacts versus live HACS setup."""
    docs_text = GALLERY_DOC_PATH.read_text(encoding="utf-8")

    assert "Phase 1" in docs_text
    assert "Phase 2" in docs_text
    assert "HACS" in docs_text
    assert "does not bundle third-party JavaScript" in docs_text
    assert "replace every `weather.twc` reference" in docs_text
    assert "optional extra entities" in docs_text
    assert "Sections view" in docs_text


def test_weather_card_gallery_dependency_doc_covers_custom_resources() -> None:
    """Dependency doc should list every custom card resource needed by the gallery."""
    docs_text = GALLERY_DEPENDENCY_DOC_PATH.read_text(encoding="utf-8")

    for resource in (
        "simple-weather-card-bundle.js",
        "hourly-weather.js",
        "clock-weather-card.js",
        "twc-simple-weather-card-compat.js",
        "bom-weather-card.js",
        "weather_icons",
        "platinum-weather-card.js",
        "ha-card-weather-conditions.js",
        "lovelace-horizon-card.js",
        "weather-radar-card.js",
        "meteoalarm-card.js",
    ):
        assert resource in docs_text

    assert "Fork Candidates" in docs_text
    assert "Supervisor add-ons cannot be installed" in docs_text


def test_simple_weather_card_compat_resource_patches_locale_lookup() -> None:
    """Simple Weather Card compatibility shim should guard modern HA localization."""
    resource_text = SIMPLE_WEATHER_COMPAT_RESOURCE_PATH.read_text(encoding="utf-8")

    assert 'customElements.whenDefined("simple-weather-card")' in resource_text
    assert "prototype.toLocale" in resource_text
    assert "hass?.resources" in resource_text
    assert "hass?.localize" in resource_text


def test_weather_card_gallery_marks_hacs_installed_cards() -> None:
    """Cards installed in the test instance should be marked as HACS installed."""
    yaml_text = GALLERY_DASHBOARD_PATH.read_text(encoding="utf-8")
    docs_text = GALLERY_DOC_PATH.read_text(encoding="utf-8")
    dependency_text = GALLERY_DEPENDENCY_DOC_PATH.read_text(encoding="utf-8")

    assert "| Simple Weather Card | Installed via HACS |" in yaml_text
    assert "| Hourly Weather Card | Installed via HACS |" in yaml_text
    assert "| Clock Weather Card | Installed via HACS |" in yaml_text
    assert "| Simple Weather Card | `custom:simple-weather-card` | Installed via HACS |" in docs_text
    assert "/hacsfiles/simple-weather-card/simple-weather-card-bundle.js" in dependency_text
    assert "/hacsfiles/lovelace-hourly-weather/hourly-weather.js" in dependency_text
    assert "/hacsfiles/clock-weather-card/clock-weather-card.js" in dependency_text
