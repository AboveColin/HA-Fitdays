"""Base entity for the Fitdays integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FitdaysDataUpdateCoordinator
from .const import DOMAIN, MANUFACTURER


class FitdaysEntity(CoordinatorEntity[FitdaysDataUpdateCoordinator]):
    """
    An entity belonging to one member profile.

    Each profile on the account becomes its own Home Assistant device, so a
    household sharing a scale gets one device per person rather than a single
    blob of ambiguous sensors.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FitdaysDataUpdateCoordinator,
        entry_id: str,
        suid: str,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._suid = suid
        self._key = key
        self._attr_unique_id = f"{entry_id}_{suid}_{key}"

    @property
    def _profile_data(self) -> dict[str, Any]:
        """The coordinator slice for this profile."""
        profiles = (self.coordinator.data or {}).get("profiles") or {}
        return profiles.get(self._suid) or {}

    @property
    def _profile(self) -> Any:
        """The :class:`fitdays.UserProfile` for this entity."""
        return self._profile_data.get("profile")

    @property
    def _latest(self) -> Any:
        """The most recent measurement for this profile, if any."""
        return self._profile_data.get("latest")

    @property
    def _scale(self) -> Any:
        """The first scale bound to the account, used for device metadata."""
        devices = (self.coordinator.data or {}).get("devices") or []
        return devices[0] if devices else None

    @property
    def device_info(self) -> DeviceInfo:
        """Describe this profile as a device."""
        profile = self._profile
        scale = self._scale
        name = profile.display_name if profile else f"Profile {self._suid}"
        info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry_id}_{self._suid}")},
            manufacturer=MANUFACTURER,
            name=name,
            model=(scale.model or scale.name) if scale else "Fitdays scale",
        )
        if scale and scale.serial:
            info["serial_number"] = scale.serial
        if scale and scale.firmware_version:
            info["sw_version"] = scale.firmware_version
        return info

    @property
    def available(self) -> bool:
        """Available while the account still reports this profile."""
        return self.coordinator.last_update_success and bool(self._profile_data)
