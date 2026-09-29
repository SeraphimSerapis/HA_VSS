"""Config flow for the VSS integration."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from vss import ApiDeclarations

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import AUTH_FAILURE_CODES
from .device import VSSConfigEntry

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate the credentials were rejected."""


class InvalidHost(HomeAssistantError):
    """Error to indicate there is an invalid hostname."""


class InvalidPort(HomeAssistantError):
    """Error to indicate there is an invalid port."""


async def validate_input(hass: HomeAssistant, data: Mapping[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect.

    Data has the keys from the user schema with values provided by the user.
    """
    host = data["host"]
    port = data.get("port", "8081")
    client_id = data["client_id"]
    client_secret = data["client_secret"]

    try:
        port_int = int(port)
    except ValueError as err:
        raise InvalidPort from err
    if not 1 <= port_int <= 65535:
        raise InvalidPort

    if len(host) < 3:
        raise InvalidHost

    vss_api = ApiDeclarations(f"{host}:{port}/", client_id, client_secret)

    try:
        status_code, _response = await asyncio.wait_for(
            hass.async_add_executor_job(vss_api.get_all_devices),
            timeout=10,
        )
    except (TimeoutError, OSError) as err:
        raise CannotConnect from err

    if status_code in AUTH_FAILURE_CODES:
        raise InvalidAuth
    if status_code != 200:
        _LOGGER.error("Could not connect to VSS (status code %s)", status_code)
        raise CannotConnect

    return {"title": "VSS"}


def _error_for(err: Exception) -> str:
    """Map a validation exception to a translation key."""
    if isinstance(err, CannotConnect):
        return "cannot_connect"
    if isinstance(err, InvalidAuth):
        return "invalid_auth"
    if isinstance(err, InvalidHost):
        return "invalid_host"
    if isinstance(err, InvalidPort):
        return "invalid_port"
    _LOGGER.exception("Unexpected exception", exc_info=err)
    return "unknown"


_VALIDATION_ERRORS = (CannotConnect, InvalidAuth, InvalidHost, InvalidPort, Exception)


class VSSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for VSS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input["host"])
            self._abort_if_unique_id_configured()
            try:
                info = await validate_input(self.hass, user_input)
            except _VALIDATION_ERRORS as err:
                errors["base"] = _error_for(err)
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        schema = vol.Schema(
            {
                vol.Required("host"): str,
                vol.Optional("port", default="8081"): str,
                vol.Required("client_id"): str,
                vol.Required("client_secret"): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication after the server rejected the credentials."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for new API credentials."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_input(self.hass, {**entry.data, **user_input})
            except _VALIDATION_ERRORS as err:
                errors["base"] = _error_for(err)
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates=user_input
                )

        schema = vol.Schema(
            {
                vol.Required("client_id"): str,
                vol.Required("client_secret"): str,
            }
        )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or {"client_id": entry.data["client_id"]}
            ),
            description_placeholders={"host": entry.data["host"]},
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the port or credentials of an existing entry."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_input(self.hass, {**entry.data, **user_input})
            except _VALIDATION_ERRORS as err:
                errors["base"] = _error_for(err)
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates=user_input
                )

        schema = vol.Schema(
            {
                vol.Required("port"): str,
                vol.Required("client_id"): str,
                vol.Required("client_secret"): str,
            }
        )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                schema,
                user_input
                or {
                    "port": entry.data.get("port", "8081"),
                    "client_id": entry.data["client_id"],
                },
            ),
            description_placeholders={"host": entry.data["host"]},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: VSSConfigEntry) -> VSSOptionsFlow:
        """Return the options flow."""
        return VSSOptionsFlow()


class VSSOptionsFlow(OptionsFlowWithReload):
    """Handle VSS options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(
                    NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=60,
                            step=1,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="min",
                        )
                    ),
                    vol.Coerce(int),
                ),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                schema, self.config_entry.options
            ),
        )
