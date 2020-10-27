"""A wrapper device to hold the setup information."""


class Device:
    """A dummy device"""

    def __init__(self, hass, host):
        """Init dummy hub."""
        self._host = host
        self._hass = hass
        self._name = host
        self._id = host.lower()

    @property
    def hub_id(self):
        """ID for dummy hub."""
        return self._id
