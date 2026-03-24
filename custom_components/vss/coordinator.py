"""DataUpdateCoordinator for the VSS integration."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from vss import ApiDeclarations

_LOGGER = logging.getLogger(__name__)


class VSSCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching VSS data."""

    def __init__(self, hass: HomeAssistant, vss_api: ApiDeclarations) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="VSS",
            update_interval=timedelta(minutes=5),
        )
        self._vss_api = vss_api

    async def _async_update_data(self) -> dict:
        """Fetch data from the VSS API."""
        status_code, response = await self.hass.async_add_executor_job(
            self._vss_api.get_all_devices
        )
        if status_code != 200:
            raise UpdateFailed(f"VSS API returned status code {status_code}")
        if response is None:
            raise UpdateFailed("VSS API returned no data")
        return {device["Uuid"]: device for device in response}
