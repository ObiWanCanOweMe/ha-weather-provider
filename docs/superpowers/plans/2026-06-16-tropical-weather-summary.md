# Tropical Weather Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional, compact TWC active tropical storm summary sensors without creating per-storm entities.

**Architecture:** Follow the existing pollen optional-endpoint pattern: add an options toggle, fetch tropical data only when enabled, treat endpoint access/no-data failures as non-fatal, and expose sensors only when the option is enabled. Keep storm details as attributes on one aggregate sensor so the entity registry stays stable while storms appear and disappear.

**Tech Stack:** Home Assistant custom integration, aiohttp, DataUpdateCoordinator, SensorEntity, pytest, aioresponses, voluptuous.

---

## File Structure

- Modify `custom_components/ha_weather_provider/const.py`: add `CONF_ENABLE_TROPICAL_WEATHER`.
- Modify `custom_components/ha_weather_provider/api.py`: add tropical endpoint path, query params, and `async_get_tropical_current_position()`.
- Modify `custom_components/ha_weather_provider/coordinator.py`: add `tropical_current_position` data and optional fetch behavior.
- Modify `custom_components/ha_weather_provider/__init__.py`: pass the tropical option into the coordinator.
- Modify `custom_components/ha_weather_provider/config_flow.py`: expose the tropical option in the options flow.
- Modify `custom_components/ha_weather_provider/sensor.py`: add tropical summary normalization and sensors.
- Modify `custom_components/ha_weather_provider/strings.json` and `custom_components/ha_weather_provider/translations/en.json`: add option labels/descriptions.
- Modify `docs/weather-card-gallery-dependencies.md`: document tropical summary sensors.
- Modify tests in `tests/test_api.py`, `tests/test_coordinator.py`, `tests/test_init.py`, `tests/test_config_flow.py`, and `tests/test_sensor.py`.

---

### Task 1: API Client Tropical Current Position Endpoint

**Files:**
- Modify: `custom_components/ha_weather_provider/api.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write the failing API endpoint test**

Add `TROPICAL_CURRENT_POSITION_PATH` to the import list in `tests/test_api.py`.

Add this test after the pollen tests:

```python
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
```

- [ ] **Step 2: Write the failing non-fatal endpoint test**

Add this parametrized test:

```python
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
```

- [ ] **Step 3: Run the API tests and verify they fail**

Run:

`PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_api.py::test_async_get_tropical_current_position_calls_twc_tropical_endpoint tests/test_api.py::test_async_get_tropical_current_position_returns_empty_for_unavailable_endpoint -q`

Expected: fail because `TROPICAL_CURRENT_POSITION_PATH` and `async_get_tropical_current_position` do not exist.

- [ ] **Step 4: Implement the API path, params, and method**

In `custom_components/ha_weather_provider/api.py`, add:

```python
TROPICAL_CURRENT_POSITION_PATH = "/v2/tropical/currentposition"
```

Add this property to `TWCClient`:

```python
@property
def _tropical_query_params(self) -> dict[str, str]:
    return {
        "apiKey": self._api_key,
        "source": "default",
        "basin": "all",
        "language": self._language,
        "format": "json",
        "units": self._units,
        "nautical": "false",
    }
```

Add this method near the optional endpoint methods:

```python
async def async_get_tropical_current_position(self) -> dict[str, Any]:
    """Return active tropical storm current-position data, when available."""
    try:
        return await self._async_get_json(
            TROPICAL_CURRENT_POSITION_PATH, params=self._tropical_query_params
        )
    except (TWCAuthError, TWCNoDataError, TWCPermissionError):
        return {}
```

- [ ] **Step 5: Run the API tests and verify they pass**

Run:

`PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_api.py::test_async_get_tropical_current_position_calls_twc_tropical_endpoint tests/test_api.py::test_async_get_tropical_current_position_returns_empty_for_unavailable_endpoint -q`

Expected: pass.

- [ ] **Step 6: Commit API client changes**

Run:

```bash
git add custom_components/ha_weather_provider/api.py tests/test_api.py
git commit -m "Add tropical current position API client"
```

---

### Task 2: Options Flow And Setup Wiring

**Files:**
- Modify: `custom_components/ha_weather_provider/const.py`
- Modify: `custom_components/ha_weather_provider/config_flow.py`
- Modify: `custom_components/ha_weather_provider/__init__.py`
- Modify: `custom_components/ha_weather_provider/strings.json`
- Modify: `custom_components/ha_weather_provider/translations/en.json`
- Test: `tests/test_config_flow.py`
- Test: `tests/test_init.py`

- [ ] **Step 1: Write failing options flow tests**

In `tests/test_config_flow.py`, import `CONF_ENABLE_TROPICAL_WEATHER`.

Update existing options-flow expected data dictionaries to include:

```python
CONF_ENABLE_TROPICAL_WEATHER: False
```

Add this test near the pollen options test:

```python
async def test_options_flow_configures_tropical_weather(hass):
    """Options flow stores the tropical weather toggle."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_DAILY_FORECAST_DURATION: "7day",
            CONF_EXTRA_ENTITIES: True,
            CONF_ENABLE_POLLEN: False,
            CONF_ENABLE_TROPICAL_WEATHER: True,
            CONF_HOURLY_FORECAST_DURATION: "2day",
            CONF_UPDATE_INTERVAL_MINUTES: 30,
        },
    )

    assert result["type"] == "create_entry"
    assert result["data"][CONF_ENABLE_TROPICAL_WEATHER] is True
```

- [ ] **Step 2: Write failing setup wiring tests**

In `tests/test_init.py`, import `CONF_ENABLE_TROPICAL_WEATHER`.

Add:

```python
@pytest.mark.asyncio
async def test_async_setup_entry_passes_tropical_option_to_coordinator(hass):
    """Setup should pass the selected tropical weather option into the coordinator."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={CONF_ENABLE_TROPICAL_WEATHER: True},
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "custom_components.ha_weather_provider.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.TWCClient", return_value=object()
    ), patch(
        "custom_components.ha_weather_provider.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_coordinator.call_args.kwargs["tropical_enabled"] is True
```

Add:

```python
@pytest.mark.asyncio
async def test_async_setup_entry_disables_tropical_by_default(hass):
    """Setup should leave tropical weather disabled unless selected."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_API_KEY: "secret",
            CONF_LATITUDE: 40.58,
            CONF_LONGITUDE: -111.66,
            CONF_UNITS: "e",
            CONF_LANGUAGE: "en-US",
        },
        options={},
    )
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "custom_components.ha_weather_provider.async_get_clientsession",
        return_value=object(),
    ), patch(
        "custom_components.ha_weather_provider.TWCClient", return_value=object()
    ), patch(
        "custom_components.ha_weather_provider.TWCWeatherCoordinator",
        return_value=coordinator,
    ) as mock_coordinator, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
    ):
        await async_setup_entry(hass, entry)

    assert mock_coordinator.call_args.kwargs["tropical_enabled"] is False
```

- [ ] **Step 3: Run options/setup tests and verify they fail**

Run:

`PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_config_flow.py tests/test_init.py -q`

Expected: fail because `CONF_ENABLE_TROPICAL_WEATHER` and coordinator wiring are missing.

- [ ] **Step 4: Implement constants, option schema, and setup wiring**

In `custom_components/ha_weather_provider/const.py`, add:

```python
CONF_ENABLE_TROPICAL_WEATHER = "enable_tropical_weather"
```

In `custom_components/ha_weather_provider/config_flow.py`, import the constant and add this option after `CONF_ENABLE_POLLEN`:

```python
vol.Optional(
    CONF_ENABLE_TROPICAL_WEATHER,
    default=self.config_entry.options.get(CONF_ENABLE_TROPICAL_WEATHER, False),
): bool,
```

In `custom_components/ha_weather_provider/__init__.py`, import the constant and add:

```python
def _entry_enable_tropical_weather(entry: ConfigEntry) -> bool:
    """Return whether optional tropical weather data is enabled."""
    options = getattr(entry, "options", {})
    return options.get(CONF_ENABLE_TROPICAL_WEATHER) is True
```

Pass it to the coordinator:

```python
tropical_enabled=_entry_enable_tropical_weather(entry),
```

In `strings.json` and `translations/en.json`, add to option `data`:

```json
"enable_tropical_weather": "Enable tropical weather"
```

Add to option `data_description`:

```json
"enable_tropical_weather": "Requests The Weather Company tropical current-position endpoint and creates compact active storm summary sensors when data is available."
```

- [ ] **Step 5: Run options/setup tests and verify they pass**

Run:

`PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_config_flow.py tests/test_init.py -q`

Expected: pass.

- [ ] **Step 6: Commit options/setup changes**

Run:

```bash
git add custom_components/ha_weather_provider/const.py custom_components/ha_weather_provider/config_flow.py custom_components/ha_weather_provider/__init__.py custom_components/ha_weather_provider/strings.json custom_components/ha_weather_provider/translations/en.json tests/test_config_flow.py tests/test_init.py
git commit -m "Add tropical weather option"
```

---

### Task 3: Coordinator Optional Tropical Fetch

**Files:**
- Modify: `custom_components/ha_weather_provider/coordinator.py`
- Test: `tests/test_coordinator.py`

- [ ] **Step 1: Write failing coordinator tests**

Update `test_coordinator_combines_current_and_forecast` expected `TWCWeatherData` to include:

```python
tropical_current_position={},
```

Add:

```python
@pytest.mark.asyncio
async def test_coordinator_fetches_tropical_when_enabled(hass) -> None:
    """Coordinator should merge tropical current-position data when enabled."""
    client = AsyncMock()
    client.async_get_current_conditions.return_value = {"temperature": 72}
    client.async_get_daily_forecast.return_value = {"temperatureMax": [75]}
    client.async_get_hourly_forecast.return_value = {"temperature": [72, 71]}
    client.async_get_alert_headlines.return_value = {"alerts": []}
    client.async_get_tropical_current_position.return_value = {
        "currentPosition": [{"storm_id": "AL012026"}]
    }
    coordinator = TWCWeatherCoordinator(hass, client, tropical_enabled=True)

    data = await coordinator._async_update_data()

    assert data.tropical_current_position == {
        "currentPosition": [{"storm_id": "AL012026"}]
    }
    client.async_get_tropical_current_position.assert_awaited_once()
```

Add:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        TWCNoDataError("empty"),
        TWCAuthError("bad key for optional endpoint"),
        TWCPermissionError("no access"),
        TWCRequestError("temporary tropical failure"),
    ],
)
async def test_coordinator_keeps_weather_data_when_optional_tropical_unavailable(
    hass, error
) -> None:
    """Optional tropical endpoint failures should not fail weather refresh."""
    client = AsyncMock()
    client.async_get_current_conditions.return_value = {"temperature": 72}
    client.async_get_daily_forecast.return_value = {"temperatureMax": [75]}
    client.async_get_hourly_forecast.return_value = {"temperature": [72, 71]}
    client.async_get_alert_headlines.return_value = {"alerts": []}
    client.async_get_tropical_current_position.side_effect = error
    coordinator = TWCWeatherCoordinator(hass, client, tropical_enabled=True)

    data = await coordinator._async_update_data()

    assert data.current == {"temperature": 72}
    assert data.tropical_current_position == {}
```

- [ ] **Step 2: Run coordinator tests and verify they fail**

Run:

`PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_coordinator.py -q`

Expected: fail because `tropical_enabled`, `tropical_current_position`, and the tropical client call are missing.

- [ ] **Step 3: Implement coordinator tropical data**

In `TWCWeatherData`, add:

```python
tropical_current_position: dict[str, Any] = field(default_factory=dict)
```

In `TWCWeatherCoordinator.__init__`, add keyword arg and assignment:

```python
tropical_enabled: bool = False,
```

```python
self.tropical_enabled = tropical_enabled
```

In `_async_update_data()`, after pollen handling or alongside it, add:

```python
tropical_current_position: dict[str, Any] = {}
if self.tropical_enabled:
    try:
        tropical_current_position = await self.client.async_get_tropical_current_position()
    except TWCError:
        _LOGGER.debug("Optional TWC tropical current-position endpoint is unavailable")
```

Add to returned `TWCWeatherData`:

```python
tropical_current_position=tropical_current_position,
```

- [ ] **Step 4: Run coordinator tests and verify they pass**

Run:

`PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_coordinator.py -q`

Expected: pass.

- [ ] **Step 5: Commit coordinator changes**

Run:

```bash
git add custom_components/ha_weather_provider/coordinator.py tests/test_coordinator.py
git commit -m "Fetch tropical weather data optionally"
```

---

### Task 4: Tropical Summary Sensor Entities

**Files:**
- Modify: `custom_components/ha_weather_provider/sensor.py`
- Test: `tests/test_sensor.py`

- [ ] **Step 1: Write failing sensor setup test**

In `tests/test_sensor.py`, import `CONF_ENABLE_TROPICAL_WEATHER`.

Update `_coordinator()` signature:

```python
def _coordinator(
    *,
    daily_forecast: dict[str, object] | None = None,
    pollen_forecast: dict[str, object] | None = None,
    tropical_current_position: dict[str, object] | None = None,
) -> SimpleNamespace:
```

Pass it into `TWCWeatherData`:

```python
tropical_current_position=tropical_current_position or {},
```

Add:

```python
async def test_sensor_setup_adds_tropical_entities_when_tropical_enabled(hass) -> None:
    """Tropical sensors should be created when the tropical option is enabled."""
    async_add_entities = Mock()
    entry = _entry(
        options={CONF_ENABLE_TROPICAL_WEATHER: True, CONF_EXTRA_ENTITIES: False}
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _coordinator()

    await async_setup_entry(hass, entry, async_add_entities)

    entities = async_add_entities.call_args.args[0]
    assert [entity.unique_id for entity in entities] == [
        "entry-id_tropical_active_storm_count",
        "entry-id_tropical_active_storms",
        "entry-id_tropical_last_update_time",
        "entry-id_tropical_expiration_time",
    ]
```

- [ ] **Step 2: Write failing tropical sensor value test**

Add:

```python
def test_tropical_sensor_values() -> None:
    """Tropical sensors should expose compact active storm summaries."""
    coordinator = _coordinator(
        tropical_current_position={
            "currentPosition": [
                {
                    "storm_id": "AL012026",
                    "storm_key": "storm-key-1",
                    "storm_name": "Alex",
                    "basin": "AL",
                    "storm_type": "Tropical Storm",
                    "storm_sub_type": "Category 1 Hurricane",
                    "lat": 24.5,
                    "lon": -72.3,
                    "max_sustained_wind": 65,
                    "wind_gust": 80,
                    "min_pressure": 992,
                    "expire_time_gmt": 1781712000,
                    "headline": ["Alex remains offshore."],
                    "advisory_info": {
                        "advisory_time_epoch": 1781701200,
                        "process_time_epoch": 1781706300,
                    },
                    "heading": {
                        "storm_dir_cardinal": "NW",
                        "storm_speed": 12,
                    },
                }
            ]
        }
    )
    entry = _entry(options={CONF_ENABLE_TROPICAL_WEATHER: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.tropical_entity_descriptions()
        ]
    }

    assert entities["tropical_active_storm_count"].native_value == 1
    assert entities["tropical_active_storms"].native_value == "1 active storm"
    assert entities["tropical_active_storms"].extra_state_attributes == {
        "storms": [
            {
                "storm_id": "AL012026",
                "storm_key": "storm-key-1",
                "name": "Alex",
                "basin": "AL",
                "type": "Tropical Storm",
                "category": "Category 1 Hurricane",
                "latitude": 24.5,
                "longitude": -72.3,
                "max_sustained_wind": 65,
                "wind_gust": 80,
                "minimum_pressure": 992,
                "movement_direction": "NW",
                "movement_speed": 12,
                "advisory_time": "2026-06-17T13:00:00+00:00",
                "expires": "2026-06-17T16:00:00+00:00",
                "headline": "Alex remains offshore.",
            }
        ]
    }
    assert entities["tropical_last_update_time"].native_value == datetime(
        2026, 6, 17, 13, 0, tzinfo=UTC
    )
    assert entities["tropical_last_update_time"].device_class == SensorDeviceClass.TIMESTAMP
    assert entities["tropical_expiration_time"].native_value == datetime(
        2026, 6, 17, 16, 0, tzinfo=UTC
    )
```

- [ ] **Step 3: Write failing empty payload test**

Add:

```python
def test_tropical_sensor_values_are_empty_when_payload_is_missing() -> None:
    """Tropical sensors should expose no-active-storm state for absent endpoint data."""
    coordinator = _coordinator(tropical_current_position={})
    entry = _entry(options={CONF_ENABLE_TROPICAL_WEATHER: True})

    entities = {
        entity.entity_description.key: entity
        for entity in [
            TWCSensorEntity(coordinator, entry, description)
            for description in TWCSensorEntity.tropical_entity_descriptions()
        ]
    }

    assert entities["tropical_active_storm_count"].native_value == 0
    assert entities["tropical_active_storms"].native_value == "No active storms"
    assert entities["tropical_active_storms"].extra_state_attributes == {"storms": []}
    assert entities["tropical_last_update_time"].native_value is None
    assert entities["tropical_expiration_time"].native_value is None
```

- [ ] **Step 4: Run sensor tests and verify they fail**

Run:

`PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_sensor.py::test_sensor_setup_adds_tropical_entities_when_tropical_enabled tests/test_sensor.py::test_tropical_sensor_values tests/test_sensor.py::test_tropical_sensor_values_are_empty_when_payload_is_missing -q`

Expected: fail because tropical descriptions and helpers do not exist.

- [ ] **Step 5: Implement description support for attributes**

In `TWCSensorEntityDescription`, add:

```python
attr_fn: Callable[[TWCWeatherData], dict[str, Any]] | None = None
```

In `TWCSensorEntity`, add:

```python
@property
def extra_state_attributes(self) -> dict[str, Any] | None:
    """Return sensor attributes, when configured."""
    if self.entity_description.attr_fn is None:
        return None
    return self.entity_description.attr_fn(self.coordinator.data)
```

- [ ] **Step 6: Implement tropical normalization helpers**

In `sensor.py`, add these helpers near pollen helpers:

```python
def _tropical_records(data: TWCWeatherData) -> list[dict[str, Any]]:
    """Return tropical current-position records from supported payload shapes."""
    payload = data.tropical_current_position
    for key in ("currentPosition", "current_position", "storms"):
        records = payload.get(key)
        if isinstance(records, list):
            return [record for record in records if isinstance(record, dict)]
    if any(isinstance(value, list) for value in payload.values()):
        lengths = [
            len(value) for value in payload.values() if isinstance(value, list)
        ]
        if not lengths:
            return []
        records: list[dict[str, Any]] = []
        for index in range(max(lengths)):
            record = {
                key: value[index]
                for key, value in payload.items()
                if isinstance(value, list) and index < len(value)
            }
            if record:
                records.append(record)
        return records
    return []
```

```python
def _first_value(record: dict[str, Any], *keys: str) -> Any:
    """Return the first present non-empty value from a tropical record."""
    for key in keys:
        value = record.get(key)
        if value is not None and value != "":
            return value
    return None
```

```python
def _nested_first_value(record: dict[str, Any], parent: str, *keys: str) -> Any:
    """Return the first non-empty nested value from a tropical record."""
    nested = record.get(parent)
    if not isinstance(nested, dict):
        return None
    return _first_value(nested, *keys)
```

```python
def _iso_timestamp(value: Any) -> str | None:
    """Return an epoch value as an ISO timestamp string."""
    timestamp = _timestamp_from_epoch(value)
    return timestamp.isoformat() if timestamp is not None else None
```

```python
def _headline_value(value: Any) -> Any:
    """Return a single headline from string or list payload values."""
    if isinstance(value, list):
        return next((item for item in value if item), None)
    return value if value != "" else None
```

```python
def _tropical_storm_summaries(data: TWCWeatherData) -> list[dict[str, Any]]:
    """Return normalized active tropical storm summaries."""
    summaries: list[dict[str, Any]] = []
    for record in _tropical_records(data):
        summary = {
            "storm_id": _first_value(record, "storm_id", "stormId"),
            "storm_key": _first_value(record, "storm_key", "stormKey"),
            "name": _first_value(record, "storm_name", "stormName"),
            "basin": _first_value(record, "basin"),
            "type": _first_value(record, "storm_type", "stormType"),
            "category": _first_value(record, "storm_sub_type", "stormSubType"),
            "latitude": _first_value(record, "lat", "latitude"),
            "longitude": _first_value(record, "lon", "longitude"),
            "max_sustained_wind": _first_value(
                record, "max_sustained_wind", "maxSustainedWind"
            ),
            "wind_gust": _first_value(record, "wind_gust", "windGust"),
            "minimum_pressure": _first_value(record, "min_pressure", "minimumPressure"),
            "movement_direction": _first_value(record, "storm_dir_cardinal"),
            "movement_speed": _first_value(record, "storm_speed"),
            "advisory_time": _iso_timestamp(
                _first_value(record, "advisory_time_epoch", "advisoryTimeEpoch")
                or _nested_first_value(
                    record,
                    "advisory_info",
                    "advisory_time_epoch",
                    "process_time_epoch",
                )
            ),
            "expires": _iso_timestamp(
                _first_value(record, "expire_time_gmt", "expireTimeGmt")
            ),
            "headline": _headline_value(_first_value(record, "headline")),
        }
        heading = record.get("heading")
        if isinstance(heading, dict):
            summary["movement_direction"] = summary["movement_direction"] or _first_value(
                heading, "storm_dir_cardinal", "stormDirectionCardinal"
            )
            summary["movement_speed"] = summary["movement_speed"] or _first_value(
                heading, "storm_speed", "stormSpeed"
            )
        summaries.append(
            {key: value for key, value in summary.items() if value is not None}
        )
    return summaries
```

```python
def _tropical_storm_count(data: TWCWeatherData) -> int:
    """Return the number of active tropical storm summaries."""
    return len(_tropical_storm_summaries(data))
```

```python
def _tropical_storm_state(data: TWCWeatherData) -> str:
    """Return a compact active tropical storm state string."""
    count = _tropical_storm_count(data)
    if count == 0:
        return "No active storms"
    if count == 1:
        return "1 active storm"
    return f"{count} active storms"
```

```python
def _tropical_storm_attributes(data: TWCWeatherData) -> dict[str, Any]:
    """Return active tropical storm summaries as sensor attributes."""
    return {"storms": _tropical_storm_summaries(data)}
```

```python
def _tropical_first_timestamp(data: TWCWeatherData, *keys: str) -> datetime | None:
    """Return the earliest available timestamp value from tropical records."""
    for record in _tropical_records(data):
        for key in keys:
            value = _first_value(record, key)
            timestamp = _timestamp_from_epoch(value)
            if timestamp is not None:
                return timestamp
        nested = record.get("advisory_info")
        if isinstance(nested, dict):
            for key in keys:
                timestamp = _timestamp_from_epoch(_first_value(nested, key))
                if timestamp is not None:
                    return timestamp
    return None
```

- [ ] **Step 7: Add tropical sensor descriptions**

Add:

```python
TROPICAL_SENSOR_DESCRIPTIONS: tuple[TWCSensorEntityDescription, ...] = (
    TWCSensorEntityDescription(
        key="tropical_active_storm_count",
        name="Tropical Active Storm Count",
        icon="mdi:weather-hurricane",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_tropical_storm_count,
    ),
    TWCSensorEntityDescription(
        key="tropical_active_storms",
        name="Tropical Active Storms",
        icon="mdi:weather-hurricane",
        value_fn=_tropical_storm_state,
        attr_fn=_tropical_storm_attributes,
    ),
    TWCSensorEntityDescription(
        key="tropical_last_update_time",
        name="Tropical Last Update Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _tropical_first_timestamp(
            data,
            "advisory_time_epoch",
            "advisoryTimeEpoch",
            "process_time_epoch",
            "processTimeEpoch",
        ),
    ),
    TWCSensorEntityDescription(
        key="tropical_expiration_time",
        name="Tropical Expiration Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _tropical_first_timestamp(
            data,
            "expire_time_gmt",
            "expireTimeGmt",
        ),
    ),
)
```

In `async_setup_entry`, extend descriptions when enabled:

```python
if entry.options.get(CONF_ENABLE_TROPICAL_WEATHER, False):
    descriptions.extend(TROPICAL_SENSOR_DESCRIPTIONS)
```

Add static method:

```python
@staticmethod
def tropical_entity_descriptions() -> tuple[TWCSensorEntityDescription, ...]:
    """Return optional TWC tropical sensor descriptions."""
    return TROPICAL_SENSOR_DESCRIPTIONS
```

- [ ] **Step 8: Run sensor tests and verify they pass**

Run:

`PYTHONPATH=. .worktrees/demo-dashboard-card/.venv/bin/pytest tests/test_sensor.py::test_sensor_setup_adds_tropical_entities_when_tropical_enabled tests/test_sensor.py::test_tropical_sensor_values tests/test_sensor.py::test_tropical_sensor_values_are_empty_when_payload_is_missing -q`

Expected: pass.

- [ ] **Step 9: Commit sensor changes**

Run:

```bash
git add custom_components/ha_weather_provider/sensor.py tests/test_sensor.py
git commit -m "Add tropical summary sensors"
```

---

### Task 5: Documentation And Verification

**Files:**
- Modify: `docs/weather-card-gallery-dependencies.md`
- Verify: full project checks

- [ ] **Step 1: Update dependency documentation**

In `docs/weather-card-gallery-dependencies.md`, update the `Tropical Weather` row to mention the first slice:

```markdown
| Tropical Weather | `docs/twc_api/API - Standard - Tropical - *.pdf`, `docs/twc_api/API - Standard - v3 - Tropical Models - *.pdf` | First slice: optional compact active storm summary sensors from current-position data: `sensor.twc_tropical_active_storm_count`, `sensor.twc_tropical_active_storms`, `sensor.twc_tropical_last_update_time`, and `sensor.twc_tropical_expiration_time`. Later slices can add cone/path/bulletin/model detail. |
```

- [ ] **Step 2: Run formatting and lint checks**

Run:

`.worktrees/demo-dashboard-card/.venv/bin/ruff check custom_components/ha_weather_provider/api.py custom_components/ha_weather_provider/config_flow.py custom_components/ha_weather_provider/coordinator.py custom_components/ha_weather_provider/__init__.py custom_components/ha_weather_provider/sensor.py tests/test_api.py tests/test_config_flow.py tests/test_coordinator.py tests/test_init.py tests/test_sensor.py`

Expected: `All checks passed!`

- [ ] **Step 3: Run the full project check**

Run:

`PATH=".worktrees/demo-dashboard-card/.venv/bin:$PATH" python3 /Users/akener/.codex/plugins/cache/personal/obi-dev-harness/0.1.0+codex.20260610212042/scripts/harness.py project-check .`

Expected: all project checks pass and pytest reports all tests passing.

- [ ] **Step 4: Commit documentation after verification**

Run:

```bash
git add docs/weather-card-gallery-dependencies.md
git commit -m "Document tropical summary sensor slice"
```

- [ ] **Step 5: Optional live HA reload**

If the user wants the feature live in the test instance after implementation, restart the HA test container:

```bash
docker restart ha-weather-provider-test
```

Then enable `Enable tropical weather` in integration options. If direct storage editing is used, stop HA first, back up `/Users/akener/.ha-weather-provider-test/config/.storage/core.config_entries`, add `"enable_tropical_weather": true` to the TWC entry options, and start HA again.

Confirm registry entries:

```bash
rg -n 'sensor\\.twc_tropical_' /Users/akener/.ha-weather-provider-test/config/.storage/core.entity_registry
```

Expected: four tropical sensors are registered when the option is enabled. In the current test API entitlement state, tropical sensors may show no active storms or unavailable endpoint-derived timestamps.
