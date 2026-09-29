"""The VSS integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from vss import ApiDeclarations

from .const import DOMAIN
from .coordinator import VSSCoordinator
from .device import VSSConfigEntry, VSSData

PLATFORMS = ["binary_sensor", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: VSSConfigEntry) -> bool:
    """Set up VSS from a config entry."""
    host = entry.data["host"]
    port = entry.data.get("port", "8081")
    client_id = entry.data["client_id"]
    client_secret = entry.data["client_secret"]

    vss_api = ApiDeclarations(f"{host}:{port}/", client_id, client_secret)

    coordinator = VSSCoordinator(hass, entry, vss_api)
    await coordinator.async_config_entry_first_refresh()

    device_registry = dr.async_get(hass)
    hub = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, host.lower())},
        manufacturer="Visionect",
        name=host,
        model="VSS Hub",
    )

    entry.runtime_data = VSSData(coordinator=coordinator, hub_device_id=hub.id)

    @callback
    def _remove_stale_devices() -> None:
        """Drop devices for displays the server no longer reports."""
        if not coordinator.data:
            return
        for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
            if device.id == hub.id:
                continue
            uuids = {ident for domain, ident in device.identifiers if domain == DOMAIN}
            if uuids and uuids.isdisjoint(coordinator.data):
                device_registry.async_update_device(
                    device.id, remove_config_entry_id=entry.entry_id
                )

    _remove_stale_devices()
    entry.async_on_unload(coordinator.async_add_listener(_remove_stale_devices))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: VSSConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: VSSConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Allow removing displays the server no longer reports (never the hub)."""
    if device_entry.id == entry.runtime_data.hub_device_id:
        return False
    return not any(
        domain == DOMAIN and ident in entry.runtime_data.coordinator.data
        for domain, ident in device_entry.identifiers
    )
