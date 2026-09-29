"""Runtime data shared by the VSS platforms."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from .coordinator import VSSCoordinator


@dataclass
class VSSData:
    """Objects created during setup and stored on the config entry."""

    coordinator: VSSCoordinator
    hub_device_id: str


type VSSConfigEntry = ConfigEntry[VSSData]
