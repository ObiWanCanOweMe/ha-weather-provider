"""Tests for the TWC API client."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import ClientError, ClientSession
from aioresponses import aioresponses
from yarl import URL

from custom_components.ha_weather_provider import api
from custom_components.ha_weather_provider.api import (
    CURRENT_PATH,
    DAILY_FORECAST_PATH,
    HOURLY_FORECAST_PATH,
    TWCAuthError,
    TWCClient,
    TWCError,
    TWCNoDataError,
    TWCRequestError,
    TWCPermissionError,
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


def _request_url(url: str, *, include_units: bool = True) -> str:
    query = {
        "apiKey": API_KEY,
        "geocode": "40.58%2C-111.66",
        "language": LANGUAGE,
        "format": "json",
    }
    if include_units:
        query["units"] = UNITS
    return str(URL(url).with_query(query))


def _assert_request(
    mocked: aioresponses, method: str, url: str, *, include_units: bool = True
) -> None:
    assert len(mocked.requests) == 1
    (actual_method, actual_url), calls = next(iter(mocked.requests.items()))
    assert actual_method == method
    assert actual_url.scheme == "https"
    assert actual_url.host == URL(url).host
    assert actual_url.path == URL(url).path
    request = calls[0]
    expected_params = {
        "apiKey": API_KEY,
        "geocode": f"{LATITUDE},{LONGITUDE}",
        "language": LANGUAGE,
        "format": "json",
    }
    if include_units:
        expected_params["units"] = UNITS
    assert request.kwargs["params"] == expected_params
    assert request.kwargs["headers"] == {"Accept-Encoding": "gzip"}


@pytest.mark.asyncio
async def test_async_get_current_conditions_calls_twc_current_endpoint() -> None:
    """Current conditions call the expected endpoint and return the payload."""
    url = f"{api.BASE_URL}{CURRENT_PATH}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(_request_url(url), payload={"temperature": 72})

            payload = await client.async_get_current_conditions()

    assert payload == {"temperature": 72}
    _assert_request(mocked, "GET", url)


@pytest.mark.asyncio
async def test_async_get_daily_forecast_calls_twc_daily_forecast_endpoint() -> None:
    """Daily forecast call returns the payload from the expected endpoint."""
    url = f"{api.BASE_URL}{DAILY_FORECAST_PATH}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(
                _request_url(url),
                payload={"forecasts": [{"day": "today"}]},
            )

            payload = await client.async_get_daily_forecast()

    assert payload == {"forecasts": [{"day": "today"}]}
    _assert_request(mocked, "GET", url)


@pytest.mark.asyncio
async def test_async_get_hourly_forecast_calls_twc_hourly_forecast_endpoint() -> None:
    """Hourly forecast call returns the payload from the expected endpoint."""
    url = f"{api.BASE_URL}{HOURLY_FORECAST_PATH}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(
                _request_url(url),
                payload={"validTimeUtc": [1718121600]},
            )

            payload = await client.async_get_hourly_forecast()

    assert payload == {"validTimeUtc": [1718121600]}
    _assert_request(mocked, "GET", url)


@pytest.mark.asyncio
async def test_async_get_alert_headlines_calls_twc_alert_headlines_endpoint() -> None:
    """Alert headlines call returns the payload from the expected endpoint."""
    url = f"{api.BASE_URL}{api.ALERT_HEADLINES_PATH}"
    payload = {"alerts": [{"eventDescription": "Tornado Warning"}]}
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(_request_url(url, include_units=False), payload=payload)

            result = await client.async_get_alert_headlines()

    assert result == payload
    _assert_request(mocked, "GET", url, include_units=False)


@pytest.mark.asyncio
async def test_async_get_alert_headlines_returns_empty_alerts_for_no_data() -> None:
    """A 204 alert headline response means there are no active alerts."""
    url = f"{api.BASE_URL}{api.ALERT_HEADLINES_PATH}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(_request_url(url, include_units=False), status=204)

            result = await client.async_get_alert_headlines()

    assert result == {"alerts": []}
    _assert_request(mocked, "GET", url, include_units=False)


@pytest.mark.asyncio
async def test_async_get_daily_forecast_maps_http_status_errors() -> None:
    """Daily forecast errors use the same request failure mapping."""
    url = f"{api.BASE_URL}{DAILY_FORECAST_PATH}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(_request_url(url), status=503)

            with pytest.raises(TWCRequestError):
                await client.async_get_daily_forecast()


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
    url = f"{api.BASE_URL}{CURRENT_PATH}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(_request_url(url), status=status)

            with pytest.raises(error_type):
                await client.async_get_current_conditions()


@pytest.mark.asyncio
async def test_async_get_current_conditions_maps_client_errors() -> None:
    """aiohttp client failures are wrapped as TWC request errors."""
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(_request_url(f"{api.BASE_URL}{CURRENT_PATH}"), exception=ClientError())

            with pytest.raises(TWCRequestError):
                await client.async_get_current_conditions()


@pytest.mark.asyncio
async def test_async_get_current_conditions_maps_timeout_errors() -> None:
    """aiohttp timeouts are wrapped as TWC request errors."""
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(
                _request_url(f"{api.BASE_URL}{CURRENT_PATH}"),
                exception=asyncio.TimeoutError(),
            )

            with pytest.raises(TWCRequestError):
                await client.async_get_current_conditions()
