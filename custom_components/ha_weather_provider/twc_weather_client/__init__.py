"""The Weather Company async client and payload helpers."""

from __future__ import annotations

from .defaults import (
    DEFAULT_AIR_QUALITY_SCALE,
    DEFAULT_DAILY_FORECAST_DURATION,
    DEFAULT_HOURLY_FORECAST_DURATION,
    DEFAULT_POLLEN_FORECAST_DURATION,
)
from .errors import (
    TWCAuthError,
    TWCError,
    TWCNoDataError,
    TWCPermissionError,
    TWCRequestError,
)
from .normalizers import (
    CONDITION_BY_ICON,
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
from .client import TWCClient

__all__ = [
    "CONDITION_BY_ICON",
    "DEFAULT_AIR_QUALITY_SCALE",
    "DEFAULT_DAILY_FORECAST_DURATION",
    "DEFAULT_HOURLY_FORECAST_DURATION",
    "DEFAULT_POLLEN_FORECAST_DURATION",
    "TWCAuthError",
    "TWCClient",
    "TWCError",
    "TWCNoDataError",
    "TWCPermissionError",
    "TWCRequestError",
    "alert_summaries",
    "condition_from_twc",
    "first_daypart_value",
    "first_non_null",
    "forecast_datetime",
    "series_item",
    "series_value",
    "series_values",
    "value",
]
