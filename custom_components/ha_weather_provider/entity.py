"""Shared entity helpers for HA Weather Provider."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DISPLAY_NAME, DOMAIN, INTEGRATION_VERSION


def twc_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the service device shared by TWC weather and sensor entities."""
    return DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer=DISPLAY_NAME,
        name=DISPLAY_NAME,
        sw_version=INTEGRATION_VERSION,
    )
