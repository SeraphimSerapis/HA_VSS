"""Config flow for the VSS integration."""
import logging

from vss import ApiDeclarations

import voluptuous as vol

from homeassistant import config_entries, core, exceptions

from .const import DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    host = data["host"]
    port = data["port"]
    client_id = data["client_id"]
    client_secret = data["client_secret"]

    if port is None:
        port = "8081"

    if len(port) > 5:
        raise InvalidPort

    if len(host) < 3:
        raise InvalidHost

    vss_api = ApiDeclarations(f"{host}:{port}/", client_id, client_secret)

    status_code, response = await hass.async_add_executor_job(vss_api.get_all_devices)

    if not status_code == 200:
        _LOGGER.error("Could not connect to VSS")
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {"title": "VSS"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for VSS."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        DATA_SCHEMA = vol.Schema(
            {
                vol.Required("host"): str,
                vol.Optional("port", default="8081"): str,
                vol.Required("client_id"): str,
                vol.Required("client_secret"): str,
            }
        )

        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["base"] = "invalid_host"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""


class InvalidPort(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid port."""
