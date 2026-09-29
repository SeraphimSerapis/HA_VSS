"""Shared fixtures for the VSS tests."""
from __future__ import annotations

from collections.abc import Generator
from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vss.const import DOMAIN

ENTRY_DATA = {
    "host": "http://vss.local",
    "port": "8081",
    "client_id": "client-id",
    "client_secret": "client-secret",
}

DEVICE = {
    "Uuid": "uuid-1",
    "State": "Online",
    "Options": {"Name": "Kitchen", "Firmware": "1.2.3", "Revision": "R2"},
    "Status": {
        "Battery": 80,
        "Temperature": "22.5",
        "RSSI": -60,
        "Charger": 1,
        "ErrorCode": 0,
        "ConnectReason": "Wakeup",
    },
    "Displays": [{"Height": 800, "Width": 600, "Rotation": 0}],
}


def make_device(uuid: str, name: str) -> dict:
    """Return a copy of the sample device with another UUID and name."""
    device = deepcopy(DEVICE)
    device["Uuid"] = uuid
    device["Options"]["Name"] = name
    return device


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load the integration under test."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a config entry for the sample server."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="VSS",
        data=ENTRY_DATA,
        unique_id=ENTRY_DATA["host"],
    )


@pytest.fixture
def mock_api() -> Generator[MagicMock]:
    """Patch the VSS API client used by setup and the config flow."""
    with (
        patch("custom_components.vss.ApiDeclarations") as setup_api,
        patch("custom_components.vss.config_flow.ApiDeclarations", setup_api),
    ):
        client = setup_api.return_value
        client.get_all_devices.return_value = (200, [deepcopy(DEVICE)])
        yield client
