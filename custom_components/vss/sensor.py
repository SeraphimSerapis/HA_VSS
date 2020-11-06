"""Platform for VSS sensor integration."""
import logging

from homeassistant.helpers.entity import Entity

from homeassistant.const import DEVICE_CLASS_BATTERY

from vss_python_api import ApiDeclarations

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    SW_VERSION
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    host = config_entry.data["host"]
    key = config_entry.data["username"]
    secret = config_entry.data["password"]

    parent = hass.data[DOMAIN][config_entry.entry_id]

    vss_api = ApiDeclarations(host, key, secret)
    status_code, response = await hass.async_add_executor_job(
        vss_api.get_all_devices
    )

    new_devices = []
    for device in response:
        new_devices.append(VSSDisplay(device, vss_api, parent))

    if new_devices:
        async_add_devices(new_devices)


class VSSDisplay(Entity):
    """Representation of an VSS display."""

    def __init__(self, device, vss, parent):
        """Initialize the VSS display."""
        self._vss = vss
        self._device = parent
        self._device_class = DEVICE_CLASS_BATTERY
        self._unit_of_measurement = "%"
        self._icon = "mdi:tablet"
        self._display = device["Displays"][0]
        self._height = self._display["Height"]
        self._online = device["State"]
        self._rotation = self._display["Rotation"]
        self._state = device["Status"]["Battery"]
        self._uuid = device["Uuid"]
        self._width = self._display["Width"]
        self._name = None
        self._orientation = None

        if device["Options"]["Name"] is not None:
            self._name = device["Options"]["Name"]

        if self._rotation == 0 or self._rotation == 2:
            self._orientation = "Portrait"
        else:
            self._orientation = "Landscape"

        self._attributes = {
            "connected": device["State"],
            "rssi": device["Status"]["RSSI"],
            "height": self._height,
            "width": self._width,
            "orientation": self._orientation,
            "rotation": self._rotation,
        }

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, self._uuid),
            },
            "name": self._name,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": SW_VERSION,
            "via_device": (DOMAIN, self._device),
        }

    @property
    def name(self):
        """Return the display name of this sensor."""
        if self._name is not None:
            return self._name
        else:
            return self._uuid

    @property
    def unique_id(self):
        """Return the uuid of this sensor."""
        return f"{self._uuid}_sensor"

    @property
    def icon(self):
        """Return the icon for this sensor."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of the sensor."""
        return self._unit_of_measurement

    @property
    def device_state_attributes(self):
        """Return additional attributes of the sensor."""
        return self._attributes

    def update(self):
        """Fetch new state data for this sensor."""
        status_code, device = self._vss.get_device(self._uuid)

        if not status_code == 200:
            _LOGGER.error("Could not connect to VSS")
            return

        if device is None:
            _LOGGER.debug(
              "Received no data for device {id}".format(**self._uuid))
            return

        self._uuid = device["Uuid"]
        self._online = device["State"]
        self._state = device["Status"]["Battery"]
        self._display = device["Displays"][0]
        self._rotation = self._display["Rotation"]

        if device["Options"]["Name"] is not None:
            self._name = device["Options"]["Name"]

        self._orientation = "Landscape"
        if self._rotation == 0 or self._rotation == 2:
            self._orientation = "Portrait"

        self._attributes["connected"] = device["State"]
        self._attributes["rssi"] = device["Status"]["RSSI"]
        self._attributes["orientation"] = self._orientation
        self._attributes["rotation"] = self._rotation
