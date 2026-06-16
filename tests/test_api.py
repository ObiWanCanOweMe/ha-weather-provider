"""Tests for the TWC API client."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import ClientError, ClientSession
from aioresponses import aioresponses
from yarl import URL

from custom_components.ha_weather_provider import api
from custom_components.ha_weather_provider.api import (
    AIR_QUALITY_PATH,
    CURRENT_PATH,
    DAILY_FORECAST_PATH,
    HOURLY_FORECAST_PATH,
    POLLEN_FORECAST_PATH,
    POLLEN_OBSERVATION_PATH,
    TROPICAL_CURRENT_POSITION_PATH,
    TWCAuthError,
    TWCClient,
    TWCError,
    TWCNoDataError,
    TWCRequestError,
    TWCPermissionError,
)
from custom_components.ha_weather_provider.const import DEFAULT_AIR_QUALITY_SCALE


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


def _assert_pollen_observation_request(mocked: aioresponses, url: str) -> None:
    assert len(mocked.requests) == 1
    (actual_method, actual_url), calls = next(iter(mocked.requests.items()))
    assert actual_method == "GET"
    assert actual_url.scheme == "https"
    assert actual_url.host == URL(url).host
    assert actual_url.path == URL(url).path
    request = calls[0]
    assert request.kwargs["params"] == {
        "apiKey": API_KEY,
        "language": LANGUAGE,
    }
    assert request.kwargs["headers"] == {"Accept-Encoding": "gzip"}


def _assert_air_quality_request(mocked: aioresponses, url: str) -> None:
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
        "language": LANGUAGE,
        "scale": DEFAULT_AIR_QUALITY_SCALE,
        "format": "json",
    }
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
async def test_async_get_daily_forecast_uses_configured_duration() -> None:
    """Daily forecast calls the configured duration endpoint."""
    url = f"{api.BASE_URL}/v3/wx/forecast/daily/15day"
    async with ClientSession() as session:
        client = TWCClient(
            session=session,
            api_key=API_KEY,
            latitude=LATITUDE,
            longitude=LONGITUDE,
            units=UNITS,
            language=LANGUAGE,
            daily_forecast_duration="15day",
        )
        with aioresponses() as mocked:
            mocked.get(
                _request_url(url),
                payload={"forecasts": [{"day": "extended"}]},
            )

            payload = await client.async_get_daily_forecast()

    assert payload == {"forecasts": [{"day": "extended"}]}
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
async def test_async_get_hourly_forecast_uses_configured_duration() -> None:
    """Hourly forecast calls the configured duration endpoint."""
    url = f"{api.BASE_URL}/v3/wx/forecast/hourly/6hour"
    async with ClientSession() as session:
        client = TWCClient(
            session=session,
            api_key=API_KEY,
            latitude=LATITUDE,
            longitude=LONGITUDE,
            units=UNITS,
            language=LANGUAGE,
            hourly_forecast_duration="6hour",
        )
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
async def test_async_get_alert_headlines_returns_empty_alerts_for_not_found() -> None:
    """A 404 alert headline response means there is no alert data for this point."""
    url = f"{api.BASE_URL}{api.ALERT_HEADLINES_PATH}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(_request_url(url, include_units=False), status=404)

            result = await client.async_get_alert_headlines()

    assert result == {"alerts": []}
    _assert_request(mocked, "GET", url, include_units=False)


@pytest.mark.asyncio
async def test_async_get_pollen_forecast_calls_twc_pollen_endpoint() -> None:
    """Pollen forecast call returns the payload from the expected endpoint."""
    url = f"{api.BASE_URL}{POLLEN_FORECAST_PATH}"
    payload = {
        "pollenForecast12hour": {
            "fcstValid": [1741820400],
            "grassPollenIndex": [1],
            "grassPollenCategory": ["Low"],
            "treePollenIndex": [3],
            "treePollenCategory": ["High"],
            "ragweedPollenIndex": [0],
            "ragweedPollenCategory": ["None"],
        }
    }
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(_request_url(url, include_units=False), payload=payload)

            result = await client.async_get_pollen_forecast()

    assert result == payload
    _assert_request(mocked, "GET", url, include_units=False)


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [204, 403])
async def test_async_get_pollen_forecast_returns_empty_for_unavailable_endpoint(
    status: int,
) -> None:
    """Pollen endpoint no-data and entitlement failures should be non-fatal."""
    url = f"{api.BASE_URL}{POLLEN_FORECAST_PATH}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(_request_url(url, include_units=False), status=status)

            result = await client.async_get_pollen_forecast()

    assert result == {}
    _assert_request(mocked, "GET", url, include_units=False)


@pytest.mark.asyncio
async def test_async_get_pollen_observation_calls_twc_pollen_endpoint() -> None:
    """Pollen observation call returns the payload from the expected endpoint."""
    path = POLLEN_OBSERVATION_PATH.format(latitude=LATITUDE, longitude=LONGITUDE)
    url = f"{api.BASE_URL}{path}"
    payload = {
        "metadata": {"expire_time_gmt": 1397271306},
        "pollenobservations": [
            {
                "rpt_dt": "2014-04-08T15:00:00Z",
                "total_pollen_cnt": 1156,
                "total_pollen_idx": "4",
                "total_pollen_desc": "High",
                "pollenobservation": [
                    {
                        "pollen_type": "Tree",
                        "pollen_idx": "4",
                        "pollen_desc": "Very High",
                        "pollen_cnt": 1156,
                    }
                ],
            }
        ],
    }
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(
                str(
                    URL(url).with_query(
                        {
                            "apiKey": API_KEY,
                            "language": LANGUAGE,
                        }
                    )
                ),
                payload=payload,
            )

            result = await client.async_get_pollen_observation()

    assert result == payload
    _assert_pollen_observation_request(mocked, url)


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [204, 401, 403])
async def test_async_get_pollen_observation_returns_empty_for_unavailable_endpoint(
    status: int,
) -> None:
    """Pollen observation no-data and entitlement failures should be non-fatal."""
    path = POLLEN_OBSERVATION_PATH.format(latitude=LATITUDE, longitude=LONGITUDE)
    url = f"{api.BASE_URL}{path}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(
                str(
                    URL(url).with_query(
                        {
                            "apiKey": API_KEY,
                            "language": LANGUAGE,
                        }
                    )
                ),
                status=status,
            )

            result = await client.async_get_pollen_observation()

    assert result == {}
    _assert_pollen_observation_request(mocked, url)


@pytest.mark.asyncio
async def test_async_get_tropical_current_position_calls_twc_tropical_endpoint() -> None:
    """Tropical current position call returns active storm payloads."""
    url = f"{api.BASE_URL}{TROPICAL_CURRENT_POSITION_PATH}"
    payload = {
        "currentPosition": [
            {
                "storm_id": "AL012026",
                "storm_name": "Alex",
                "basin": "AL",
            }
        ]
    }
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(
                str(
                    URL(url).with_query(
                        {
                            "apiKey": API_KEY,
                            "source": "default",
                            "basin": "all",
                            "language": LANGUAGE,
                            "format": "json",
                            "units": UNITS,
                            "nautical": "false",
                        }
                    )
                ),
                payload=payload,
            )

            result = await client.async_get_tropical_current_position()

    assert result == payload
    assert len(mocked.requests) == 1
    (actual_method, actual_url), calls = next(iter(mocked.requests.items()))
    assert actual_method == "GET"
    assert actual_url.scheme == "https"
    assert actual_url.host == URL(url).host
    assert actual_url.path == URL(url).path
    request = calls[0]
    assert request.kwargs["params"] == {
        "apiKey": API_KEY,
        "source": "default",
        "basin": "all",
        "language": LANGUAGE,
        "format": "json",
        "units": UNITS,
        "nautical": "false",
    }
    assert request.kwargs["headers"] == {"Accept-Encoding": "gzip"}


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [204, 401, 403])
async def test_async_get_tropical_current_position_returns_empty_for_unavailable_endpoint(
    status: int,
) -> None:
    """Tropical endpoint no-data and entitlement failures should be non-fatal."""
    url = f"{api.BASE_URL}{TROPICAL_CURRENT_POSITION_PATH}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(
                str(
                    URL(url).with_query(
                        {
                            "apiKey": API_KEY,
                            "source": "default",
                            "basin": "all",
                            "language": LANGUAGE,
                            "format": "json",
                            "units": UNITS,
                            "nautical": "false",
                        }
                    )
                ),
                status=status,
            )

            result = await client.async_get_tropical_current_position()

    assert result == {}


@pytest.mark.asyncio
async def test_async_get_air_quality_calls_twc_air_quality_endpoint() -> None:
    """Air quality call returns the payload from the expected endpoint."""
    url = f"{api.BASE_URL}{AIR_QUALITY_PATH}"
    payload = {
        "globalairquality": {
            "airQualityIndex": 61,
            "airQualityCategory": "Moderate",
            "primaryPollutant": "PM2.5",
        }
    }
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(
                str(
                    URL(url).with_query(
                        {
                            "apiKey": API_KEY,
                            "geocode": f"{LATITUDE},{LONGITUDE}",
                            "language": LANGUAGE,
                            "scale": DEFAULT_AIR_QUALITY_SCALE,
                            "format": "json",
                        }
                    )
                ),
                payload=payload,
            )

            result = await client.async_get_air_quality()

    assert result == payload
    _assert_air_quality_request(mocked, url)


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [204, 401, 403])
async def test_async_get_air_quality_returns_empty_for_unavailable_endpoint(
    status: int,
) -> None:
    """Air quality no-data and entitlement failures should be non-fatal."""
    url = f"{api.BASE_URL}{AIR_QUALITY_PATH}"
    async with ClientSession() as session:
        client = _make_client(session)
        with aioresponses() as mocked:
            mocked.get(
                str(
                    URL(url).with_query(
                        {
                            "apiKey": API_KEY,
                            "geocode": f"{LATITUDE},{LONGITUDE}",
                            "language": LANGUAGE,
                            "scale": DEFAULT_AIR_QUALITY_SCALE,
                            "format": "json",
                        }
                    )
                ),
                status=status,
            )

            result = await client.async_get_air_quality()

    assert result == {}
    _assert_air_quality_request(mocked, url)


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
