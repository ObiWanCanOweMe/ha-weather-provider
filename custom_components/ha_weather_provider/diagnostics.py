"""Diagnostics support for HA Weather Provider."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data

from .const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, DOMAIN, INTEGRATION_VERSION

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

SECRET_KEY_FRAGMENTS = (
    CONF_API_KEY,
    "access_token",
    "refresh_token",
    "token",
    "secret",
    "password",
    "credential",
)

SENSITIVE_KEYS = {
    CONF_LATITUDE,
    CONF_LONGITUDE,
}


def _secret_keys(*mappings: dict[str, Any]) -> set[str]:
    """Return keys that should be redacted from diagnostics."""
    keys: set[str] = set()
    for mapping in mappings:
        for key in mapping:
            key_lower = str(key).lower()
            if any(fragment in key_lower for fragment in SECRET_KEY_FRAGMENTS):
                keys.add(key)
    return keys


def _payload_presence(data: Any) -> dict[str, bool]:
    """Return whether each coordinator payload is present."""
    return {
        "current": bool(data.current),
        "daily_forecast": bool(data.daily_forecast),
        "hourly_forecast": bool(data.hourly_forecast),
        "alert_headlines": bool(data.alert_headlines),
        "pollen_forecast": bool(data.pollen_forecast),
        "pollen_observation": bool(data.pollen_observation),
        "tropical_current_position": bool(data.tropical_current_position),
        "air_quality": bool(data.air_quality),
    }


def _update_interval_seconds(coordinator: Any) -> int | None:
    """Return a coordinator update interval in seconds."""
    update_interval = getattr(coordinator, "update_interval", None)
    return int(update_interval.total_seconds()) if update_interval else None


def _endpoint_coordinator_diagnostics(coordinator: Any) -> dict[str, dict[str, Any]]:
    """Return redacted diagnostics for endpoint-family coordinators."""
    endpoint_coordinators = getattr(coordinator, "endpoint_coordinators", {})
    return {
        name: {
            "last_update_success": getattr(endpoint_coordinator, "last_update_success", None),
            "update_interval_seconds": _update_interval_seconds(endpoint_coordinator),
            "has_payload": bool(getattr(endpoint_coordinator, "data", None)),
        }
        for name, endpoint_coordinator in endpoint_coordinators.items()
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = dict(entry.data)
    options = dict(entry.options)
    to_redact = SENSITIVE_KEYS | _secret_keys(data, options)
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    coordinator_data = getattr(coordinator, "data", None)

    coordinator_diagnostics: dict[str, Any] = {
        "last_update_success": getattr(coordinator, "last_update_success", None),
        "update_interval_seconds": _update_interval_seconds(coordinator),
        "enabled_optional_endpoints": {
            "pollen": bool(getattr(coordinator, "pollen_enabled", False)),
            "tropical_weather": bool(getattr(coordinator, "tropical_enabled", False)),
            "air_quality": bool(getattr(coordinator, "air_quality_enabled", False)),
        },
    }
    if coordinator_data is not None:
        coordinator_diagnostics["payloads"] = _payload_presence(coordinator_data)
    endpoint_diagnostics = _endpoint_coordinator_diagnostics(coordinator)
    if endpoint_diagnostics:
        coordinator_diagnostics["endpoint_coordinators"] = endpoint_diagnostics

    return {
        "integration_version": INTEGRATION_VERSION,
        "config_entry": {
            "entry_id": entry.entry_id,
            "data": async_redact_data(data, to_redact),
            "options": async_redact_data(options, to_redact),
        },
        "coordinator": coordinator_diagnostics,
    }
