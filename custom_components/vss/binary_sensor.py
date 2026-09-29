"""Platform for VSS binary sensor integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import VSSCoordinator
from .device import VSSConfigEntry
from .entity import VSSEntity, async_add_new_devices

PARALLEL_UPDATES = 0

CHARGER = BinarySensorEntityDescription(
    key="charger",
    translation_key="charger",
    device_class=BinarySensorDeviceClass.PLUG,
)
CONNECTED = BinarySensorEntityDescription(
    key="connected",
    translation_key="connected",
    device_class=BinarySensorDeviceClass.CONNECTIVITY,
    entity_category=EntityCategory.DIAGNOSTIC,
)

_ONLINE = {"online", "connected", "true", "1"}
_OFFLINE = {"offline", "disconnected", "false", "0"}


def _charger_is_on(data: dict[str, Any]) -> bool | None:
    """Return true if the charger is connected."""
    charger = data.get("Status", {}).get("Charger")
    if charger is None:
        return None
    try:
        return int(charger) > 0
    except (ValueError, TypeError):
        return bool(charger)


def _connected_is_on(data: dict[str, Any]) -> bool | None:
    """Return true if the server reports the display as connected."""
    state = data.get("State")
    if isinstance(state, bool):
        return state
    if state is None:
        return None
    text = str(state).strip().lower()
    if text in _ONLINE:
        return True
    if text in _OFFLINE:
        return False
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VSSConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up VSS binary sensor entities."""
    data = entry.runtime_data

    async_add_new_devices(
        entry,
        async_add_entities,
        lambda uuid, _device_data: [
            VSSBinarySensor(data.coordinator, uuid, data.hub_device_id, CHARGER),
            VSSBinarySensor(data.coordinator, uuid, data.hub_device_id, CONNECTED),
        ],
    )


class VSSBinarySensor(VSSEntity, BinarySensorEntity):
    """Representation of a VSS display binary sensor."""

    def __init__(
        self,
        coordinator: VSSCoordinator,
        uuid: str,
        hub_device_id: str,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the VSS binary sensor."""
        super().__init__(coordinator, uuid, hub_device_id, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        if self.entity_description.key == "charger":
            return _charger_is_on(self._device_data)
        return _connected_is_on(self._device_data)
