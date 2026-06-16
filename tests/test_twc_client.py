"""Tests for the packaged TWC request client."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses
from yarl import URL

from custom_components.ha_weather_provider.twc_weather_client import (
    DEFAULT_AIR_QUALITY_SCALE as CLIENT_DEFAULT_AIR_QUALITY_SCALE,
    DEFAULT_DAILY_FORECAST_DURATION as CLIENT_DEFAULT_DAILY_FORECAST_DURATION,
    DEFAULT_HOURLY_FORECAST_DURATION as CLIENT_DEFAULT_HOURLY_FORECAST_DURATION,
    DEFAULT_POLLEN_FORECAST_DURATION as CLIENT_DEFAULT_POLLEN_FORECAST_DURATION,
    TWCAuthError,
    TWCClient,
    TWCError,
    TWCNoDataError,
    TWCRequestError,
    TWCPermissionError,
    is_optional_endpoint_unavailable,
)
from custom_components.ha_weather_provider.const import (
    DEFAULT_AIR_QUALITY_SCALE,
    DEFAULT_DAILY_FORECAST_DURATION,
    DEFAULT_HOURLY_FORECAST_DURATION,
    DEFAULT_POLLEN_FORECAST_DURATION,
)
from custom_components.ha_weather_provider.twc_weather_client.client import (
    AIR_QUALITY_PATH,
    BASE_URL,
    CURRENT_PATH,
    POLLEN_FORECAST_PATH,
    POLLEN_OBSERVATION_PATH,
    TROPICAL_CURRENT_POSITION_PATH,
)


API_KEY = "secret"
LATITUDE = 40.58
LONGITUDE = -111.66
UNITS = "e"
LANGUAGE = "en-US"


def test_client_defaults_import_without_homeassistant(tmp_path: Path) -> None:
    """Client defaults import without the Home Assistant package available."""
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "custom_components")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.modules['homeassistant'] = None; "
                "import ha_weather_provider.twc_weather_client.defaults; "
                "print('ok')"
            ),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_integration_defaults_match_client_package_defaults() -> None:
    """Integration defaults are shared with the TWC client package."""
    assert DEFAULT_AIR_QUALITY_SCALE == CLIENT_DEFAULT_AIR_QUALITY_SCALE
    assert DEFAULT_DAILY_FORECAST_DURATION == CLIENT_DEFAULT_DAILY_FORECAST_DURATION
    assert DEFAULT_HOURLY_FORECAST_DURATION == CLIENT_DEFAULT_HOURLY_FORECAST_DURATION
    assert DEFAULT_POLLEN_FORECAST_DURATION == CLIENT_DEFAULT_POLLEN_FORECAST_DURATION


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (TWCNoDataError("empty"), True),
        (TWCPermissionError("no access"), True),
        (TWCAuthError("bad key"), True),
        (TWCRequestError("temporary failure"), False),
    ],
)
def test_is_optional_endpoint_unavailable_classifies_expected_errors(
    error: Exception, expected: bool
) -> None:
    """Optional endpoint helper classifies non-fatal availability failures."""
    assert is_optional_endpoint_unavailable(error) is expected


def _make_client(session: ClientSession) -> TWCClient:
    return TWCClient(
        session=session,
        api_key=API_KEY,
        latitude=LATITUDE,
        longitude=LONGITUDE,
        units=UNITS,
        language=LANGUAGE,
    )


def _request_url(url: str) -> str:
    return _url_with_query(
        url,
        {
            "apiKey": API_KEY,
            "geocode": f"{LATITUDE},{LONGITUDE}",
            "units": UNITS,
            "language": LANGUAGE,
            "format": "json",
        },
    )


def _url_with_query(url: str, params: dict[str, str]) -> str:
    return str(URL(url).with_query(params))


def _assert_current_conditions_request(mocked: aioresponses, url: str) -> None:
    assert len(mocked.requests) == 1
    (actual_method, actual_url), calls = next(iter(mocked.requests.items()))
    assert actual_method == "GET"
    assert actual_url.scheme == "https"
    assert actual_url.host == URL(url).host
    assert actual_url.path == URL(url).path
    request = calls[0]
    assert request.kwargs["params"] == {
        "apiKey": API_KEY,
        "geocode": f"{LATITUDE},{LONGITUDE}",
        "units": UNITS,
        "language": LANGUAGE,
        "format": "json",
    }
    assert request.kwargs["headers"] == {"Accept-Encoding": "gzip"}


@pytest.mark.asyncio
async def test_async_get_current_conditions_calls_twc_current_endpoint() -> None:
    """Current conditions call the expected endpoint and return the payload."""
    url = f"{BASE_URL}{CURRENT_PATH}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(_request_url(url), payload={"temperature": 72})

            payload = await client.async_get_current_conditions()

    assert payload == {"temperature": 72}
    _assert_current_conditions_request(mocked, url)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (204, TWCNoDataError),
        (401, TWCAuthError),
        (403, TWCPermissionError),
        (500, TWCRequestError),
        (503, TWCRequestError),
    ],
)
async def test_async_get_current_conditions_maps_http_status_errors(
    status: int, error_type: type[TWCError]
) -> None:
    """HTTP error responses map to the expected TWC exception types."""
    url = f"{BASE_URL}{CURRENT_PATH}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(_request_url(url), status=status)

            with pytest.raises(error_type):
                await client.async_get_current_conditions()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "path", "params"),
    [
        (
            "async_get_pollen_forecast",
            POLLEN_FORECAST_PATH,
            {
                "apiKey": API_KEY,
                "geocode": f"{LATITUDE},{LONGITUDE}",
                "language": LANGUAGE,
                "format": "json",
            },
        ),
        (
            "async_get_pollen_observation",
            POLLEN_OBSERVATION_PATH.format(
                latitude=LATITUDE,
                longitude=LONGITUDE,
            ),
            {
                "apiKey": API_KEY,
                "language": LANGUAGE,
            },
        ),
        (
            "async_get_tropical_current_position",
            TROPICAL_CURRENT_POSITION_PATH,
            {
                "apiKey": API_KEY,
                "source": "default",
                "basin": "all",
                "language": LANGUAGE,
                "format": "json",
                "units": UNITS,
                "nautical": "false",
            },
        ),
        (
            "async_get_air_quality",
            AIR_QUALITY_PATH,
            {
                "apiKey": API_KEY,
                "geocode": f"{LATITUDE},{LONGITUDE}",
                "language": LANGUAGE,
                "scale": CLIENT_DEFAULT_AIR_QUALITY_SCALE,
                "format": "json",
            },
        ),
    ],
)
async def test_optional_endpoint_methods_return_empty_payload_for_404(
    method_name: str, path: str, params: dict[str, str]
) -> None:
    """Optional endpoint methods should treat 404 as no data."""
    url = f"{BASE_URL}{path}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(_url_with_query(url, params), status=404)

            payload = await getattr(client, method_name)()

    assert payload == {}
