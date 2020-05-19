"""Platform for light integration."""
import logging

from vss_python_api import ApiDeclarations
import voluptuous as vol

from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
# Import the device class from the component that you want to support
from homeassistant.helpers.config_validation import (
    PLATFORM_SCHEMA)
from homeassistant.const import (
    ATTR_BATTERY_LEVEL,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_HOST,
    DEVICE_CLASS_BATTERY)

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    # http://IP:8081/
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_CLIENT_ID): cv.string,
    vol.Required(CONF_CLIENT_SECRET): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the VSS platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    host = config[CONF_HOST]
    key = config[CONF_CLIENT_ID]
    secret = config.get(CONF_CLIENT_SECRET)

    # Setup connection with devices/cloud
    vss_api = ApiDeclarations(host, key, secret)

    # Verify that passed in configuration works
    # if not hub.is_valid_login():
    #     _LOGGER.error("Could not connect to AwesomeLight hub")
    #     return

    # Add devices
    # add_entities(VSS(light) for light in hub.lights())

    _LOGGER.debug("Connected to api")

    status_code, response = vss_api.get_all_devices()

    if not status_code == 200:
        _LOGGER.error("Could not connect to VSS")
        return

    if response is None:
        _LOGGER.error("No response from VSS")
        return

    devices = []
    for device in response:
        _LOGGER.debug("Got device")
        _LOGGER.debug("Setting up %s ...", device)
        devices.append(VSSDisplay(device, vss_api))

    add_entities(devices)

class VSSDisplay(Entity):
    """Representation of an VSS display."""

    def __init__(self, device, vss):
        """Initialize the VSS display."""
        self._vss = vss
        self._device_class = DEVICE_CLASS_BATTERY
        self._uuid = device['Uuid']
        self._online = device["State"]
        self._state = device["Status"]["Battery"]
        self._attributes = {
            "connected": device["State"],
            "rssi": device["Status"]["RSSI"],
        }

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def name(self):
        """Return the display name of this device."""
        return self._uuid

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return additional attributes of the sensor."""
        return self._attributes

    def update(self):
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        status_code, device = self._vss.get_device(self._uuid)

        if not status_code == 200:
            _LOGGER.error("Could not connect to VSS")
            return

        if device is None:
            _LOGGER.debug("Received no data for device {id}".format(**self._uuid))
            return

        self._state = device["Status"]["Battery"]
        self._attributes = {
            "connected": device["State"],
            "rssi": device["Status"]["RSSI"],
        }
