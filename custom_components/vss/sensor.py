"""Platform for VSS sensor integration."""
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
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import VSSCoordinator
from .device import VSSConfigEntry
from .entity import VSSEntity, async_add_new_devices

PARALLEL_UPDATES = 0


def _to_float(value: Any) -> float | None:
    """Convert an API value to a float, tolerating strings and missing data."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _battery_attributes(data: dict[str, Any]) -> dict[str, Any] | None:
    """Return the legacy attributes that used to live on the battery sensor."""
    if not data:
        return None

    display = (data.get("Displays") or [{}])[0]
    status = data.get("Status", {})
    options = data.get("Options", {})
    rotation = display.get("Rotation", 0)

    attrs = {
        "connected": data.get("State"),
        "rssi": status.get("RSSI"),
        "height": display.get("Height"),
        "width": display.get("Width"),
        "orientation": "Portrait" if rotation in (0, 2) else "Landscape",
        "rotation": rotation,
        "error_code": status.get("ErrorCode"),
        "connect_reason": status.get("ConnectReason"),
        "firmware": options.get("Firmware"),
    }
    if (external_battery := status.get("ExternalBattery")) is not None:
        attrs["external_battery"] = external_battery
    return attrs


@dataclass(frozen=True, kw_only=True)
class VSSSensorDescription(SensorEntityDescription):
    """Describes a VSS sensor."""

    unique_suffix: str
    value_fn: Callable[[dict[str, Any]], Any]
    exists_fn: Callable[[dict[str, Any]], bool] = lambda _data: True
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None


SENSORS: tuple[VSSSensorDescription, ...] = (
    VSSSensorDescription(
        key="battery",
        translation_key="battery",
        # Keep the original unique ID for backward compatibility.
        unique_suffix="sensor",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:tablet",
        value_fn=lambda data: data.get("Status", {}).get("Battery"),
        attrs_fn=_battery_attributes,
    ),
    VSSSensorDescription(
        key="temperature",
        translation_key="temperature",
        unique_suffix="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _to_float(data.get("Status", {}).get("Temperature")),
    ),
    VSSSensorDescription(
        key="external_battery",
        translation_key="external_battery",
        unique_suffix="external_battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("Status", {}).get("ExternalBattery"),
        exists_fn=lambda data: data.get("Status", {}).get("ExternalBattery") is not None,
    ),
    VSSSensorDescription(
        key="rssi",
        translation_key="rssi",
        unique_suffix="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _to_float(data.get("Status", {}).get("RSSI")),
    ),
    VSSSensorDescription(
        key="firmware",
        translation_key="firmware",
        unique_suffix="firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("Options", {}).get("Firmware"),
    ),
    VSSSensorDescription(
        key="error_code",
        translation_key="error_code",
        unique_suffix="error_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("Status", {}).get("ErrorCode"),
    ),
    VSSSensorDescription(
        key="connect_reason",
        translation_key="connect_reason",
        unique_suffix="connect_reason",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("Status", {}).get("ConnectReason"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VSSConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up VSS sensor entities."""
    data = entry.runtime_data

    async_add_new_devices(
        entry,
        async_add_entities,
        lambda uuid, device_data: [
            VSSSensor(data.coordinator, uuid, data.hub_device_id, description)
            for description in SENSORS
            if description.exists_fn(device_data)
        ],
    )


class VSSSensor(VSSEntity, SensorEntity):
    """Representation of a VSS display sensor."""

    entity_description: VSSSensorDescription

    def __init__(
        self,
        coordinator: VSSCoordinator,
        uuid: str,
        hub_device_id: str,
        description: VSSSensorDescription,
    ) -> None:
        """Initialize the VSS sensor."""
        super().__init__(coordinator, uuid, hub_device_id, description.unique_suffix)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self._device_data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes of the sensor."""
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self._device_data)
