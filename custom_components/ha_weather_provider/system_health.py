"""System health support for HA Weather Provider."""

from __future__ import annotations

from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import (
    CONF_CURRENT_DETAIL_SENSORS,
    CONF_ENABLE_AIR_QUALITY,
    CONF_ENABLE_POLLEN,
    CONF_ENABLE_TROPICAL_WEATHER,
    CONF_FORECAST_ADAPTER_SENSORS,
    DOMAIN,
    INTEGRATION_VERSION,
)
from .diagnostics import _payload_presence
from .twc_weather_client.client import BASE_URL


@callback
def async_register(
    hass: HomeAssistant,
    register: system_health.SystemHealthRegistration,
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


def _enabled_options(options: dict[str, Any]) -> dict[str, bool]:
    """Return user-facing optional group settings."""
    return {
        "current_detail_sensors": options.get(CONF_CURRENT_DETAIL_SENSORS) is True,
        "forecast_adapter_sensors": options.get(CONF_FORECAST_ADAPTER_SENSORS) is True,
        "pollen": options.get(CONF_ENABLE_POLLEN) is True,
        "tropical_weather": options.get(CONF_ENABLE_TROPICAL_WEATHER) is True,
        "air_quality": options.get(CONF_ENABLE_AIR_QUALITY) is True,
    }


def _coordinator_info(coordinator: Any) -> dict[str, Any]:
    """Return redacted coordinator status for system health."""
    coordinator_data = getattr(coordinator, "data", None)
    info: dict[str, Any] = {
        "last_update_success": getattr(coordinator, "last_update_success", None),
        "enabled_optional_endpoints": {
            "pollen": bool(getattr(coordinator, "pollen_enabled", False)),
            "tropical_weather": bool(getattr(coordinator, "tropical_enabled", False)),
            "air_quality": bool(getattr(coordinator, "air_quality_enabled", False)),
        },
    }
    if coordinator_data is not None:
        info["payloads"] = _payload_presence(coordinator_data)
    return info


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Return redacted integration health details."""
    entries = hass.config_entries.async_entries(DOMAIN)
    info: dict[str, Any] = {
        "integration_version": INTEGRATION_VERSION,
        "configured_entries": len(entries),
        "can_reach_server": system_health.async_check_can_reach_url(hass, BASE_URL),
    }
    if not entries:
        return info

    entry = entries[0]
    info["configured_options"] = _enabled_options(dict(entry.options))

    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is not None:
        info["coordinator"] = _coordinator_info(coordinator)

    return info
