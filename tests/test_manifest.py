"""Tests for Home Assistant integration manifest metadata."""

from __future__ import annotations

import json
from pathlib import Path


MANIFEST_PATH = Path("custom_components/ha_weather_provider/manifest.json")


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
