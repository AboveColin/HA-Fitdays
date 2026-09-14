"""Backfill Home Assistant long-term statistics from the Fitdays cloud history.

The account keeps every weigh-in, and the coordinator already downloads
``HISTORY_DAYS`` of it on each refresh. Without this module the recorder only
sees the readings that arrive after the integration is installed, so a graph
starts empty for someone who has been standing on the scale for a year.

The import writes into the recorder's own statistics tables under each sensor's
entity id, which is what the statistics graph card and the energy-style long
term charts read. It does not write state history, so the logbook stays empty
for the past.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.recorder import DOMAIN as RECORDER_DOMAIN
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import async_import_statistics

try:  # Home Assistant 2025.11 and later
    from homeassistant.components.recorder.models import StatisticMeanType
except ImportError:  # pragma: no cover - older cores only carry has_mean
    StatisticMeanType = None  # type: ignore[assignment]
from homeassistant.components.sensor import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _hourly_buckets(
    measurements: list[Any],
    description: Any,
    profile: Any,
    profile_data: dict[str, Any],
) -> dict[datetime, list[float]]:
    """
    Group one sensor's historical values into the hours the recorder stores.

    A statistics row covers a whole hour, so two weigh-ins 20 minutes apart
    collapse into one row holding their min, max and mean.
    """
    buckets: dict[datetime, list[float]] = {}
    for measurement in measurements:
        measured_at = getattr(measurement, "measured_at", None)
        if measured_at is None:
            continue
        value = description.value_fn(measurement, profile, profile_data)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        hour = dt_util.as_utc(measured_at).replace(minute=0, second=0, microsecond=0)
        buckets.setdefault(hour, []).append(float(value))
    return buckets


def _metadata(entity_id: str, unit: str | None) -> StatisticMetaData:
    """
    Describe one sensor's statistics series.

    ``has_mean`` is the pre-2025.11 spelling and the recorder drops it in
    2026.4, so ``mean_type`` is used wherever the enum exists.
    """
    metadata: dict[str, Any] = {
        "has_sum": False,
        "name": None,
        "source": RECORDER_DOMAIN,
        "statistic_id": entity_id,
        "unit_of_measurement": unit,
    }
    if StatisticMeanType is not None:
        metadata["mean_type"] = StatisticMeanType.ARITHMETIC
    else:
        metadata["has_mean"] = True
    return metadata  # type: ignore[return-value]


def _statistics(buckets: dict[datetime, list[float]]) -> list[StatisticData]:
    """Turn hourly buckets into recorder rows, oldest first."""
    return [
        StatisticData(
            start=hour,
            min=min(values),
            max=max(values),
            mean=sum(values) / len(values),
        )
        for hour, values in sorted(buckets.items())
    ]


async def async_import_history(hass: HomeAssistant, entry: ConfigEntry) -> int:
    """
    Import every downloaded measurement as long-term statistics.

    Returns the number of hourly rows handed to the recorder. Importing the
    same hour again overwrites that row, so running this on every start costs
    a rewrite rather than a duplicate.
    """
    if RECORDER_DOMAIN not in hass.config.components:
        _LOGGER.debug("Recorder is not set up, skipping the history import")
        return 0

    # Imported here rather than at module scope: sensor.py imports the
    # coordinator from __init__.py, and __init__.py calls into this module.
    from .sensor import SENSORS  # pylint: disable=import-outside-toplevel

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    profiles = (coordinator.data or {}).get("profiles") or {}
    if not profiles:
        return 0

    registry = er.async_get(hass)
    entity_ids = {
        registry_entry.unique_id: registry_entry.entity_id
        for registry_entry in er.async_entries_for_config_entry(
            registry, entry.entry_id
        )
        # A disabled entity has no statistics table to write into.
        if registry_entry.disabled_by is None
    }

    rows = 0
    for suid, profile_data in profiles.items():
        measurements = profile_data.get("measurements") or []
        if not measurements:
            continue
        profile = profile_data.get("profile")

        for description in SENSORS:
            # Only a MEASUREMENT sensor gets mean/min/max statistics. The
            # counter and the timestamp sensors are not backfillable.
            if description.state_class != SensorStateClass.MEASUREMENT:
                continue
            entity_id = entity_ids.get(f"{entry.entry_id}_{suid}_{description.key}")
            if entity_id is None:
                continue

            buckets = _hourly_buckets(measurements, description, profile, profile_data)
            if not buckets:
                continue
            statistics = _statistics(buckets)

            metadata = _metadata(entity_id, description.native_unit_of_measurement)
            async_import_statistics(hass, metadata, statistics)
            rows += len(statistics)

    _LOGGER.debug("Queued %s hourly statistics rows for %s", rows, entry.title)
    return rows
