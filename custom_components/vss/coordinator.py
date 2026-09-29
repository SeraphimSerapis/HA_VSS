"""DataUpdateCoordinator for the VSS integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from vss import ApiDeclarations

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

AUTH_FAILURE_CODES = (401, 403)


class VSSCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinator to manage fetching VSS data, keyed by device UUID."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        vss_api: ApiDeclarations,
    ) -> None:
        """Initialize the coordinator."""
        minutes = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        super().__init__(
            hass,
            _LOGGER,
            name="VSS",
            config_entry=entry,
            update_interval=timedelta(minutes=minutes),
        )
        self._vss_api = vss_api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from the VSS API."""
        try:
            status_code, response = await self.hass.async_add_executor_job(
                self._vss_api.get_all_devices
            )
        except OSError as err:
            raise UpdateFailed(f"Error communicating with the VSS server: {err}") from err

        if status_code in AUTH_FAILURE_CODES:
            raise ConfigEntryAuthFailed(
                f"VSS API rejected the credentials (status code {status_code})"
            )
        if status_code != 200:
            raise UpdateFailed(f"VSS API returned status code {status_code}")
        if response is None:
            raise UpdateFailed("VSS API returned no data")
        return {device["Uuid"]: device for device in response}
