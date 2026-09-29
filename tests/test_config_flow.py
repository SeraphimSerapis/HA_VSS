"""Tests for the VSS config flow."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vss.const import DOMAIN

from .conftest import ENTRY_DATA


async def _start_user_flow(hass: HomeAssistant, data: dict) -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    return await hass.config_entries.flow.async_configure(result["flow_id"], data)


async def test_user_flow_creates_entry(hass: HomeAssistant, mock_api: MagicMock) -> None:
    """A valid server creates an entry."""
    result = await _start_user_flow(hass, ENTRY_DATA)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "VSS"
    assert result["data"] == ENTRY_DATA


@pytest.mark.parametrize(
    ("side_effect", "return_value", "error"),
    [
        (None, (401, None), "invalid_auth"),
        (None, (403, None), "invalid_auth"),
        (None, (500, None), "cannot_connect"),
        (ConnectionError("boom"), None, "cannot_connect"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_api: MagicMock,
    side_effect: Exception | None,
    return_value: tuple | None,
    error: str,
) -> None:
    """Rejected credentials and connection problems are reported separately."""
    mock_api.get_all_devices.side_effect = side_effect
    if return_value is not None:
        mock_api.get_all_devices.return_value = return_value

    result = await _start_user_flow(hass, ENTRY_DATA)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}


async def test_user_flow_invalid_port(hass: HomeAssistant, mock_api: MagicMock) -> None:
    """A non-numeric port is rejected before connecting."""
    result = await _start_user_flow(hass, {**ENTRY_DATA, "port": "abc"})

    assert result["errors"] == {"base": "invalid_port"}
    mock_api.get_all_devices.assert_not_called()


async def test_user_flow_duplicate_host_aborts(
    hass: HomeAssistant, mock_api: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """The same server cannot be configured twice."""
    mock_config_entry.add_to_hass(hass)

    result = await _start_user_flow(hass, ENTRY_DATA)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_updates_credentials(
    hass: HomeAssistant, mock_api: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """Reauth stores the new credentials."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"client_id": "new-id", "client_secret": "new-secret"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data["client_id"] == "new-id"
    assert mock_config_entry.data["client_secret"] == "new-secret"


async def test_options_flow_sets_scan_interval(
    hass: HomeAssistant, mock_api: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """The update interval is configurable."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"scan_interval": 15}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options["scan_interval"] == 15

    await hass.async_block_till_done()
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
