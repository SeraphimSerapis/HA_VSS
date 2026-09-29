"""Shared entity helpers for the VSS integration."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import VSSCoordinator
from .device import VSSConfigEntry


class VSSEntity(CoordinatorEntity[VSSCoordinator]):
    """Base class for entities that belong to one VSS display."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VSSCoordinator,
        uuid: str,
        hub_device_id: str,
        unique_suffix: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._uuid = uuid
        self._hub_device_id = hub_device_id
        self._attr_unique_id = f"{uuid}_{unique_suffix}"

    @property
    def _device_data(self) -> dict[str, Any]:
        """Return the current device data from the coordinator."""
        return self.coordinator.data.get(self._uuid, {})

    @property
    def available(self) -> bool:
        """Return whether the display is still reported by the server."""
        return super().available and self._uuid in self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this display."""
        data = self._device_data
        options = data.get("Options", {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._uuid)},
            name=options.get("Name") or self._uuid,
            manufacturer=MANUFACTURER,
            model=data.get("Model") or options.get("Model") or MODEL,
            sw_version=options.get("Firmware"),
            hw_version=options.get("Revision"),
            via_device_id=self._hub_device_id,
        )


@callback
def async_add_new_devices(
    entry: VSSConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
    factory: Callable[[str, dict[str, Any]], Iterable[Entity]],
) -> None:
    """Add entities for every display now and for displays that appear later."""
    coordinator = entry.runtime_data.coordinator
    known: set[str] = set()

    @callback
    def _add_new() -> None:
        new = [uuid for uuid in coordinator.data if uuid not in known]
        if not new:
            return
        known.update(new)
        async_add_entities(
            entity for uuid in new for entity in factory(uuid, coordinator.data[uuid])
        )

    _add_new()
    entry.async_on_unload(coordinator.async_add_listener(_add_new))
