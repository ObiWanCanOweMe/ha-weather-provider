"""Tests for the packaged TWC request client."""

from __future__ import annotations

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses
from yarl import URL

from custom_components.ha_weather_provider.twc_weather_client import (
    TWCAuthError,
    TWCClient,
    TWCError,
    TWCNoDataError,
    TWCRequestError,
    TWCPermissionError,
)
from custom_components.ha_weather_provider.twc_weather_client.client import (
    BASE_URL,
    CURRENT_PATH,
)


API_KEY = "secret"
LATITUDE = 40.58
LONGITUDE = -111.66
UNITS = "e"
LANGUAGE = "en-US"


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
    return str(
        URL(url).with_query(
            {
                "apiKey": API_KEY,
                "geocode": f"{LATITUDE},{LONGITUDE}",
                "units": UNITS,
                "language": LANGUAGE,
                "format": "json",
            }
        )
    )


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
