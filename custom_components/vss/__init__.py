"""The VSS integration."""
import voluptuous as vol

from homeassistant.core import HomeAssistant

from .const import DOMAIN

CONFIG_SCHEMA = vol.Schema({vol.Optional(DOMAIN): {}}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the VSS integration."""
    return True
