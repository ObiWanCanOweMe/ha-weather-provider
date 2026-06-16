"""Tests for reusable TWC payload normalizers."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from custom_components.ha_weather_provider.twc_weather_client.normalizers import (
    alert_summaries,
    condition_from_twc,
    first_daypart_value,
    first_non_null,
    forecast_datetime,
    series_item,
    series_value,
    series_values,
    value,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_value_returns_missing_and_empty_payload_values_as_none() -> None:
    """Payload value helper should hide missing and empty-string values."""
    assert value({"temperature": 72, "phrase": ""}, "temperature") == 72
    assert value({"temperature": 72, "phrase": ""}, "phrase") is None
    assert value({"temperature": 72}, "missing") is None


def test_condition_from_twc_maps_icon_codes_and_phrase_fallbacks() -> None:
    """Condition helper should map TWC codes and useful phrase fallbacks."""
    assert condition_from_twc(30, "Ignored") == "partlycloudy"
    assert condition_from_twc("bad", "Thunderstorms") == "lightning"
    assert condition_from_twc(None, "Thunderstorms with Rain") == "lightning-rainy"
    assert condition_from_twc(None, "Snow Showers") == "snowy"
    assert condition_from_twc(None, "Cloudy") == "cloudy"
    assert condition_from_twc(None, "Clear", daytime=True) == "sunny"
    assert condition_from_twc(None, "Clear", daytime=False) == "clear-night"
    assert condition_from_twc(None, "Unmapped") is None


def test_first_daypart_value_handles_sentinel_nested_and_malformed_values() -> None:
    """Daypart helper should handle TWC sentinel offsets and malformed payloads."""
    daypart = {
        "iconCode": [None, 30, 33, 12],
        "nested": [[None, "day one", "night one", "day two"]],
        "listValue": [None, [None, "first"], ["night"]],
        "empty": "",
    }

    assert first_daypart_value(daypart, "iconCode", 0) == 30
    assert first_daypart_value(daypart, "iconCode", 1) == 12
    assert first_daypart_value(daypart, "nested", 0) == "day one"
    assert first_daypart_value(daypart, "listValue", 0) == "first"
    assert first_daypart_value(daypart, "iconCode", 5) is None
    assert first_daypart_value(daypart, "missing", 0) is None
    assert first_daypart_value(None, "iconCode", 0) is None


def test_forecast_datetime_converts_valid_epoch_and_skips_bad_values() -> None:
    """Forecast datetime helper should return UTC ISO strings for valid epochs."""
    assert forecast_datetime(1718121600) == "2024-06-11T16:00:00+00:00"
    assert forecast_datetime("1718121600") is None
    assert forecast_datetime(None) is None


def test_series_helpers_normalize_forecast_series_values() -> None:
    """Series helpers should return list values and hide malformed entries."""
    payload = {
        "temperature": [70, "", None, True, 74.5],
        "phrase": ["Clear", "", "Cloudy"],
        "malformed": "bad",
    }

    assert series_values(payload["temperature"]) == [70, "", None, True, 74.5]
    assert series_values(payload["malformed"]) == []
    assert series_item(series_values(payload["temperature"]), 0) == 70
    assert series_item(series_values(payload["temperature"]), 4) == 74.5
    assert series_item(series_values(payload["temperature"]), 1) is None
    assert series_item(series_values(payload["temperature"]), 3) is None
    assert series_item(series_values(payload["temperature"]), 99) is None
    assert series_value(payload, "phrase", 0) == "Clear"
    assert series_value(payload, "phrase", 1) is None
    assert series_value(payload, "phrase", 99) is None


def test_first_non_null_returns_first_present_payload_value() -> None:
    """First non-null helper should skip None and empty strings."""
    assert first_non_null(None, "", 0, "fallback") == 0
    assert first_non_null(None, "") is None


def test_alert_summaries_returns_stable_alert_attribute_payloads() -> None:
    """Alert summaries should keep stable keys and skip malformed alert entries."""
    assert alert_summaries(
        {
            "alerts": [
                "bad",
                {
                    "detailKey": "abc123",
                    "eventDescription": "Tornado Warning",
                    "headlineText": "Tornado Warning until 7:30 PM",
                    "severity": "Severe",
                    "severityCode": 1,
                    "urgency": "Expected",
                    "certainty": "Observed",
                    "expireTimeLocal": "2026-06-13T19:30:00-04:00",
                    "source": "",
                },
            ]
        }
    ) == [
        {
            "detail_key": "abc123",
            "event": "Tornado Warning",
            "headline": "Tornado Warning until 7:30 PM",
            "severity": "Severe",
            "severity_code": 1,
            "urgency": "Expected",
            "certainty": "Observed",
            "expires": "2026-06-13T19:30:00-04:00",
            "source": None,
        }
    ]
    assert alert_summaries({"alerts": {}}) == []


def test_normalizers_import_without_aiohttp_or_homeassistant() -> None:
    """Normalizer imports should not load integration-only dependencies."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "custom_components")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.modules['homeassistant'] = None; "
                "sys.modules['aiohttp'] = None; "
                "import ha_weather_provider.twc_weather_client.normalizers; "
                "print('ok')"
            ),
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.stdout == "ok\n"
