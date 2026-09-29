"""Tests for setting up and running the VSS integration."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.vss.const import DOMAIN

from .conftest import DEVICE, make_device


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def _refresh(hass: HomeAssistant) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=6))
    await hass.async_block_till_done()


async def test_setup_creates_entities_and_hub_link(
    hass: HomeAssistant, mock_api: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """A display gets its sensors, linked to the hub device."""
    await _setup(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.kitchen_battery").state == "80"
    assert float(hass.states.get("sensor.kitchen_temperature").state) == 22.5
    assert hass.states.get("binary_sensor.kitchen_charger").state == "on"
    assert hass.states.get("binary_sensor.kitchen_connected").state == "on"

    devices = dr.async_get(hass)
    entry_id = mock_config_entry.entry_id
    display = devices.async_get_device_by_identifier((DOMAIN, "uuid-1"), entry_id)
    hub = devices.async_get_device_by_identifier((DOMAIN, "http://vss.local"), entry_id)
    assert display is not None and hub is not None
    assert display.via_device_id == hub.id

    # RSSI is a diagnostic entity that is disabled by default.
    entities = er.async_get(hass)
    rssi = entities.async_get_entity_id("sensor", DOMAIN, "uuid-1_rssi")
    assert rssi is not None
    assert entities.async_get(rssi).disabled


async def test_legacy_unique_ids_are_kept(
    hass: HomeAssistant, mock_api: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """Existing installs keep their entities across the refactor."""
    await _setup(hass, mock_config_entry)

    entities = er.async_get(hass)
    assert entities.async_get_entity_id("sensor", DOMAIN, "uuid-1_sensor")
    assert entities.async_get_entity_id("sensor", DOMAIN, "uuid-1_temperature")
    assert entities.async_get_entity_id("binary_sensor", DOMAIN, "uuid-1_charger")


async def test_new_display_appears_without_reload(
    hass: HomeAssistant, mock_api: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """A display added on the server shows up after the next update."""
    await _setup(hass, mock_config_entry)
    assert hass.states.get("sensor.hallway_battery") is None

    mock_api.get_all_devices.return_value = (
        200,
        [DEVICE, make_device("uuid-2", "Hallway")],
    )
    await _refresh(hass)

    assert hass.states.get("sensor.hallway_battery") is not None


async def test_removed_display_is_cleaned_up(
    hass: HomeAssistant, mock_api: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """A display that disappears from the server loses its device."""
    mock_api.get_all_devices.return_value = (
        200,
        [DEVICE, make_device("uuid-2", "Hallway")],
    )
    await _setup(hass, mock_config_entry)
    devices = dr.async_get(hass)
    entry_id = mock_config_entry.entry_id
    assert devices.async_get_device_by_identifier((DOMAIN, "uuid-2"), entry_id)

    mock_api.get_all_devices.return_value = (200, [DEVICE])
    await _refresh(hass)

    assert devices.async_get_device_by_identifier((DOMAIN, "uuid-2"), entry_id) is None
    assert devices.async_get_device_by_identifier((DOMAIN, "uuid-1"), entry_id)


async def test_rejected_credentials_start_reauth(
    hass: HomeAssistant, mock_api: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """A 401 from the server puts the entry into reauth."""
    mock_api.get_all_devices.return_value = (401, None)

    await _setup(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert any(flow["context"]["source"] == "reauth" for flow in flows)


async def test_connection_error_retries_setup(
    hass: HomeAssistant, mock_api: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """A network failure during setup is retried."""
    mock_api.get_all_devices.side_effect = ConnectionError("boom")

    await _setup(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload(
    hass: HomeAssistant, mock_api: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """The entry unloads cleanly."""
    await _setup(hass, mock_config_entry)

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_empty_displays_list_does_not_break_attributes(
    hass: HomeAssistant, mock_api: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """A display without geometry still produces a battery sensor."""
    device = make_device("uuid-1", "Kitchen")
    device["Displays"] = []
    mock_api.get_all_devices.return_value = (200, [device])

    await _setup(hass, mock_config_entry)

    state = hass.states.get("sensor.kitchen_battery")
    assert state is not None
    assert state.attributes["orientation"] == "Portrait"
