"""Tests for repository metadata and local development helpers."""

from __future__ import annotations

import json
from pathlib import Path

from packaging.version import Version


HACS_PATH = Path("hacs.json")
DEVELOP_SCRIPT = Path("scripts/develop")


def test_hacs_metadata_declares_distribution_requirements() -> None:
    """HACS metadata declares display name and minimum supported versions."""
    metadata = json.loads(HACS_PATH.read_text(encoding="utf-8"))

    assert metadata["name"] == "The Weather Company"
    assert Version(metadata["homeassistant"]) >= Version("2026.3.2")
    assert Version(metadata["hacs"]) >= Version("2.0.5")


def test_develop_script_uses_custom_component_pythonpath() -> None:
    """The development helper starts Home Assistant with custom components."""
    script = DEVELOP_SCRIPT.read_text(encoding="utf-8")

    assert "PYTHONPATH" in script
    assert "custom_components" in script
    assert "hass --config" in script
