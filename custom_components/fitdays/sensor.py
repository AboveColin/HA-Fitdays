"""Sensor platform for the Fitdays integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfMass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FitdaysDataUpdateCoordinator
from .const import DOMAIN
from .entity import FitdaysEntity


@dataclass(frozen=True, kw_only=True)
class FitdaysSensorDescription(SensorEntityDescription):
    """Describes a Fitdays sensor and how to read its value."""

    #: Called with (latest_measurement, profile, profile_data).
    value_fn: Callable[[Any, Any, dict[str, Any]], Any]


def _measure(attr: str) -> Callable[[Any, Any, dict[str, Any]], Any]:
    """Read an attribute straight off the latest measurement."""

    def _get(latest: Any, _profile: Any, _data: dict[str, Any]) -> Any:
        return getattr(latest, attr, None) if latest else None

    return _get


def _weight_to_target(latest: Any, profile: Any, _data: dict[str, Any]) -> Any:
    """How far the latest weight sits above (positive) the profile's goal."""
    if not latest or not profile:
        return None
    if latest.weight_kg is None or not profile.target_weight_kg:
        return None
    return round(latest.weight_kg - profile.target_weight_kg, 2)


SENSORS: tuple[FitdaysSensorDescription, ...] = (
    FitdaysSensorDescription(
        key="weight",
        translation_key="weight",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_measure("weight_kg"),
    ),
    FitdaysSensorDescription(
        key="bmi",
        translation_key="bmi",
        icon="mdi:human",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_measure("bmi"),
    ),
    FitdaysSensorDescription(
        key="body_fat",
        translation_key="body_fat",
        icon="mdi:percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_measure("body_fat_pct"),
    ),
    FitdaysSensorDescription(
        key="body_fat_mass",
        translation_key="body_fat_mass",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_measure("body_fat_kg"),
    ),
    FitdaysSensorDescription(
        key="muscle",
        translation_key="muscle",
        icon="mdi:arm-flex",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_measure("muscle_pct"),
    ),
    FitdaysSensorDescription(
        key="muscle_mass",
        translation_key="muscle_mass",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_measure("muscle_mass_kg"),
    ),
    FitdaysSensorDescription(
        key="skeletal_muscle",
        translation_key="skeletal_muscle",
        icon="mdi:arm-flex-outline",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_measure("skeletal_muscle_pct"),
    ),
    FitdaysSensorDescription(
        key="body_water",
        translation_key="body_water",
        icon="mdi:water-percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_measure("body_water_pct"),
    ),
    FitdaysSensorDescription(
        key="bone_mass",
        translation_key="bone_mass",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=_measure("bone_mass_kg"),
    ),
    FitdaysSensorDescription(
        key="protein",
        translation_key="protein",
        icon="mdi:food-drumstick",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_measure("protein_pct"),
    ),
    FitdaysSensorDescription(
        key="visceral_fat",
        translation_key="visceral_fat",
        icon="mdi:stomach",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_measure("visceral_fat"),
    ),
    FitdaysSensorDescription(
        key="bmr",
        translation_key="bmr",
        icon="mdi:fire",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_measure("bmr"),
    ),
    FitdaysSensorDescription(
        key="body_age",
        translation_key="body_age",
        icon="mdi:calendar-account",
        native_unit_of_measurement="y",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_measure("body_age"),
    ),
    FitdaysSensorDescription(
        key="last_measurement",
        translation_key="last_measurement",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_measure("measured_at"),
    ),
    # --- less commonly needed, off by default ----------------------------
    FitdaysSensorDescription(
        key="subcutaneous_fat",
        translation_key="subcutaneous_fat",
        icon="mdi:percent-outline",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
        value_fn=_measure("subcutaneous_fat_pct"),
    ),
    FitdaysSensorDescription(
        key="skeletal_muscle_mass",
        translation_key="skeletal_muscle_mass",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
        value_fn=_measure("skeletal_muscle_kg"),
    ),
    FitdaysSensorDescription(
        key="body_water_mass",
        translation_key="body_water_mass",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
        value_fn=_measure("body_water_kg"),
    ),
    FitdaysSensorDescription(
        key="protein_mass",
        translation_key="protein_mass",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        entity_registry_enabled_default=False,
        value_fn=_measure("protein_kg"),
    ),
    FitdaysSensorDescription(
        key="heart_rate",
        translation_key="heart_rate",
        icon="mdi:heart-pulse",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_measure("heart_rate"),
    ),
    FitdaysSensorDescription(
        key="impedance",
        translation_key="impedance",
        icon="mdi:omega",
        native_unit_of_measurement="Ω",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_measure("impedance"),
    ),
    FitdaysSensorDescription(
        key="target_weight",
        translation_key="target_weight",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
        value_fn=lambda _l, profile, _d: getattr(profile, "target_weight_kg", None),
    ),
    FitdaysSensorDescription(
        key="weight_to_target",
        translation_key="weight_to_target",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
        value_fn=_weight_to_target,
    ),
    FitdaysSensorDescription(
        key="measurement_count",
        translation_key="measurement_count",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda _l, _p, data: data.get("count"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fitdays sensors for every member profile on the account."""
    coordinator: FitdaysDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    known: set[str] = set()

    @callback
    def _add_new_profiles() -> None:
        """Create entities for profiles we have not seen yet."""
        profiles = (coordinator.data or {}).get("profiles") or {}
        new = [suid for suid in profiles if suid not in known]
        if not new:
            return
        known.update(new)
        async_add_entities(
            FitdaysSensor(coordinator, entry.entry_id, suid, description)
            for suid in new
            for description in SENSORS
        )

    _add_new_profiles()
    # A profile added in the app later should show up without a reload.
    entry.async_on_unload(coordinator.async_add_listener(_add_new_profiles))


class FitdaysSensor(FitdaysEntity, SensorEntity):
    """A single body-composition metric for one member profile."""

    entity_description: FitdaysSensorDescription

    def __init__(
        self,
        coordinator: FitdaysDataUpdateCoordinator,
        entry_id: str,
        suid: str,
        description: FitdaysSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry_id, suid, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Read this sensor's value out of the latest measurement."""
        return self.entity_description.value_fn(
            self._latest, self._profile, self._profile_data
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose measurement context on the primary weight sensor."""
        if self.entity_description.key != "weight":
            return None
        latest = self._latest
        profile = self._profile
        data = self._profile_data
        first = data.get("first_measured_at")
        return {
            "measurements": data.get("count"),
            "first_measurement": first.isoformat() if first else None,
            "height_cm": getattr(profile, "height_cm", None),
            "weight_only": getattr(latest, "is_weight_only", None),
        }
