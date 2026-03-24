"""Platform for VSS sensor integration."""
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import VSSCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up VSS sensor entities."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    parent = data["device"]

    new_devices = []
    for uuid in coordinator.data:
        new_devices.append(VSSBatterySensor(coordinator, uuid, parent))
        new_devices.append(VSSTemperatureSensor(coordinator, uuid, parent))

    if new_devices:
        async_add_devices(new_devices)


class VSSBaseSensor(CoordinatorEntity[VSSCoordinator], SensorEntity):
    """Base class for VSS sensors."""

    _sensor_type: str = ""

    def __init__(self, coordinator: VSSCoordinator, uuid: str, parent):
        """Initialize the VSS sensor."""
        super().__init__(coordinator)
        self._uuid = uuid
        self._parent = parent

    @property
    def _device_data(self):
        """Return the current device data from the coordinator."""
        return self.coordinator.data.get(self._uuid, {})

    @property
    def name(self) -> str:
        """Return the display name of this sensor."""
        data = self._device_data
        name = data.get("Options", {}).get("Name")
        base = name if name else self._uuid
        return f"{base} {self._sensor_type}"

    @property
    def device_info(self):
        """Return device info for this sensor."""
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


class VSSBatterySensor(VSSBaseSensor):
    """Representation of a VSS display battery sensor."""

    _sensor_type = "Battery"

    def __init__(self, coordinator: VSSCoordinator, uuid: str, parent):
        """Initialize the VSS battery sensor."""
        super().__init__(coordinator, uuid, parent)
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:tablet"
        # Keep original unique_id for backward compatibility
        self._attr_unique_id = f"{uuid}_sensor"

    @property
    def native_value(self):
        """Return the battery level."""
        data = self._device_data
        return data.get("Status", {}).get("Battery")

    @property
    def extra_state_attributes(self):
        """Return additional attributes of the sensor."""
        data = self._device_data
        if not data:
            return None

        display = data.get("Displays", [{}])[0]
        status = data.get("Status", {})
        options = data.get("Options", {})
        rotation = display.get("Rotation", 0)

        if rotation in (0, 2):
            orientation = "Portrait"
        else:
            orientation = "Landscape"

        attrs = {
            "connected": data.get("State"),
            "rssi": status.get("RSSI"),
            "height": display.get("Height"),
            "width": display.get("Width"),
            "orientation": orientation,
            "rotation": rotation,
            "error_code": status.get("ErrorCode"),
            "connect_reason": status.get("ConnectReason"),
            "firmware": options.get("Firmware"),
        }

        external_battery = status.get("ExternalBattery")
        if external_battery is not None:
            attrs["external_battery"] = external_battery

        return attrs


class VSSTemperatureSensor(VSSBaseSensor):
    """Representation of a VSS display temperature sensor."""

    _sensor_type = "Temperature"

    def __init__(self, coordinator: VSSCoordinator, uuid: str, parent):
        """Initialize the VSS temperature sensor."""
        super().__init__(coordinator, uuid, parent)
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_unique_id = f"{uuid}_temperature"

    @property
    def native_value(self):
        """Return the device temperature."""
        data = self._device_data
        temp = data.get("Status", {}).get("Temperature")
        if temp is not None:
            try:
                return float(temp)
            except (ValueError, TypeError):
                return None
        return None
