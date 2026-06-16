"""Tests for support and operations documentation."""

from __future__ import annotations

from pathlib import Path


OPERATIONS_DOC = Path("docs/operations.md")


def test_operations_doc_covers_polling_and_optional_endpoints() -> None:
    """Operations docs explain refresh behavior and endpoint fan-out."""
    text = OPERATIONS_DOC.read_text(encoding="utf-8")

    assert "Default refresh interval" in text
    assert "Required endpoints" in text
    assert "Optional endpoints" in text
    assert "API key entitlement" in text
    assert "Polling model" in text
    assert "/v3/wx/observations/current" in text
    assert "/v3/wx/forecast/daily" in text
    assert "/v3/wx/forecast/hourly" in text
    assert "/v3/alerts/headlines" in text
    assert "/v3/wx/globalAirQuality" in text
    assert "/v2/indices/pollen/daypart" in text
    assert "/v1/geocode" in text
    assert "/v2/tropical/currentposition" in text
