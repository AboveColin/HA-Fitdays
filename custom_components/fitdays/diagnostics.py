"""Diagnostics support for the Fitdays integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {
    "token",
    "refresh_token",
    "password_hash",
    "email",
    "uid",
    "suid",
    "active_suid",
    "mac",
    "sn",
    "serial",
    "data_id",
    "device_id",
    "nickname",
    "photo",
    "birthday",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    data = coordinator.data or {}

    profiles = []
    # Numbered by position rather than by suid: the account-internal profile id
    # identifies a person and adds nothing to a bug report.
    for index, slice_ in enumerate((data.get("profiles") or {}).values(), start=1):
        latest = slice_.get("latest")
        profile = slice_.get("profile")
        profiles.append(
            {
                "profile": index,
                "measurements": slice_.get("count"),
                "has_height": bool(getattr(profile, "height_cm", None)),
                "has_target_weight": bool(getattr(profile, "target_weight_kg", None)),
                "latest": None
                if latest is None
                else {
                    "measured_at": latest.measured_at.isoformat()
                    if latest.measured_at
                    else None,
                    "weight_only": latest.is_weight_only,
                    # Which metrics the scale actually delivered. Deliberately
                    # booleans, not values: diagnostics get pasted into public
                    # issue trackers, and someone's body-fat percentage has no
                    # business being there. This still answers the only
                    # question a bug report needs — did the field arrive?
                    "fields_present": {
                        name: getattr(latest, name, None) is not None
                        for name in (
                            "weight_kg",
                            "bmi",
                            "body_fat_pct",
                            "subcutaneous_fat_pct",
                            "visceral_fat",
                            "muscle_pct",
                            "skeletal_muscle_pct",
                            "body_water_pct",
                            "bone_mass_kg",
                            "protein_pct",
                            "bmr",
                            "body_age",
                            "heart_rate",
                            "impedance",
                        )
                    },
                },
            }
        )

    devices = [
        {
            "name": device.name,
            "model": device.model,
            "device_type": device.device_type,
            "firmware_version": device.firmware_version,
            "measures_heart_rate": device.measures_heart_rate,
            "offline_measure": device.offline_measure,
        }
        for device in (data.get("devices") or [])
    ]

    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "total_measurements": data.get("total_measurements"),
            "profile_count": len(data.get("profiles") or {}),
        },
        "profiles": async_redact_data({"profiles": profiles}, TO_REDACT)["profiles"],
        "devices": devices,
    }
