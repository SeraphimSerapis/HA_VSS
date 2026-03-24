"""The VSS integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from vss import ApiDeclarations

from .const import DOMAIN
from .coordinator import VSSCoordinator
from .device import Device

PLATFORMS = ["binary_sensor", "sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the VSS integration."""
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up VSS from a config entry."""
    host = entry.data["host"]
    port = entry.data.get("port", "8081")
    client_id = entry.data["client_id"]
    client_secret = entry.data["client_secret"]

    vss_api = ApiDeclarations(f"{host}:{port}/", client_id, client_secret)

    coordinator = VSSCoordinator(hass, vss_api)
    await coordinator.async_config_entry_first_refresh()

    device = Device(hass, host)

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "device": device,
    }

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, host.lower())},
        manufacturer="Visionect",
        name=host,
        model="VSS Hub",
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
