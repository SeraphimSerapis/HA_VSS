"""Platform for VSS binary sensor integration."""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import VSSCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up VSS binary sensor entities."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    parent = data["device"]

    new_devices = []
    for uuid in coordinator.data:
        new_devices.append(VSSChargerBinarySensor(coordinator, uuid, parent))

    if new_devices:
        async_add_devices(new_devices)


class VSSChargerBinarySensor(CoordinatorEntity[VSSCoordinator], BinarySensorEntity):
    """Representation of a VSS display charger status."""

    def __init__(self, coordinator: VSSCoordinator, uuid: str, parent):
        """Initialize the VSS charger binary sensor."""
        super().__init__(coordinator)
        self._uuid = uuid
        self._parent = parent
        self._attr_device_class = BinarySensorDeviceClass.PLUG
        self._attr_unique_id = f"{uuid}_charger"

    @property
    def _device_data(self):
        """Return the current device data from the coordinator."""
        return self.coordinator.data.get(self._uuid, {})

    @property
    def name(self) -> str:
        """Return the display name of this binary sensor."""
        data = self._device_data
        name = data.get("Options", {}).get("Name")
        if name:
            return f"{name} Charger"
        return f"{self._uuid} Charger"

    @property
    def device_info(self):
        """Return device info for this binary sensor."""
        data = self._device_data
        options = data.get("Options", {})
        return {
            "identifiers": {
                (DOMAIN, self._uuid),
            },
            "name": options.get("Name") or self._uuid,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": options.get("Firmware"),
            "hw_version": options.get("Revision"),
            "via_device": (DOMAIN, self._parent.hub_id),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the charger is connected."""
        data = self._device_data
        charger = data.get("Status", {}).get("Charger")
        if charger is None:
            return None
        try:
            return int(charger) > 0
        except (ValueError, TypeError):
            return bool(charger)
