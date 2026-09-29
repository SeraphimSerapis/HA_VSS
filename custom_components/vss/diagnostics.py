"""Diagnostics support for the VSS integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .device import VSSConfigEntry

TO_REDACT_ENTRY = {"host", "client_id", "client_secret"}
TO_REDACT_DEVICE = {"Uuid", "Name", "Mac", "IpAddress"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: VSSConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT_ENTRY),
        "options": dict(entry.options),
        "last_update_success": coordinator.last_update_success,
        "devices": [
            async_redact_data(device, TO_REDACT_DEVICE)
            for device in coordinator.data.values()
        ],
    }
