"""Tests for Home Assistant integration manifest metadata."""

from __future__ import annotations

import json
from pathlib import Path


MANIFEST_PATH = Path("custom_components/ha_weather_provider/manifest.json")
ICONS_PATH = Path("custom_components/ha_weather_provider/icons.json")


def test_manifest_declares_cloud_polling_service_metadata() -> None:
    """The integration manifest identifies this as a cloud polling service."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["iot_class"] == "cloud_polling"
    assert manifest["integration_type"] == "service"
    assert (
        manifest["issue_tracker"]
        == "https://git.kener.org/my-projects/ha-weather-provider/-/issues"
    )
    assert manifest["codeowners"] == ["@akener"]


def test_icons_metadata_declares_common_sensor_icons() -> None:
    """Icons metadata should cover common optional sensor keys."""
    icons = json.loads(ICONS_PATH.read_text(encoding="utf-8"))

    sensor_icons = icons["entity"]["sensor"]
    assert sensor_icons["condition_phrase"]["default"] == "mdi:weather-partly-cloudy"
    assert sensor_icons["wind_gust"]["default"] == "mdi:weather-windy"
    assert sensor_icons["aq_index"]["default"] == "mdi:air-filter"
    assert sensor_icons["tropical_active_storm_count"]["default"] == (
        "mdi:weather-hurricane"
    )
