"""Config flow for Solar of Things BLE."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .ble import SolarOfThingsBLEClient
from .const import CONF_ADDRESS, CONF_AES_KEY, DOMAIN
from .protocol import normalise_key

_LOGGER = logging.getLogger(__name__)


def _normalise_address(value: str) -> str:
    return value.strip().upper()


class SolarOfThingsBLEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up the local Solar of Things BLE bridge."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_address: str | None = None

    async def _async_validate(self, address: str, aes_key: str | None) -> None:
        client = SolarOfThingsBLEClient(self.hass, address, aes_key)
        try:
            if aes_key:
                await client.async_poll()
            else:
                # In keyless mode only require a real GATT connection with the
                # expected FEE7/FED5/FED6 service. The encrypted application
                # probe runs after setup and reports its own diagnostic status.
                await client.async_validate_gatt()
        finally:
            await client.async_disconnect()

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle discovery when FEE7 is advertised."""
        address = _normalise_address(discovery_info.address)
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()
        self._discovered_address = address
        self.context["title_placeholders"] = {
            "name": discovery_info.name or f"Solar BLE {address[-5:]}",
        }
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure the logger; AES is optional while reverse engineering."""
        errors: dict[str, str] = {}
        suggested_address = self._discovered_address or ""

        if user_input is not None:
            address = _normalise_address(user_input[CONF_ADDRESS])
            raw_key = str(user_input.get(CONF_AES_KEY) or "").strip()
            aes_key: str | None = None
            if raw_key:
                try:
                    aes_key = normalise_key(raw_key)
                except ValueError:
                    errors[CONF_AES_KEY] = "invalid_aes_key"

            if not errors:
                try:
                    await self._async_validate(address, aes_key)
                except Exception as err:
                    _LOGGER.debug("Solar of Things BLE validation failed: %s", err)
                    errors["base"] = "cannot_connect"
                else:
                    if self.unique_id is None:
                        await self.async_set_unique_id(address)
                        self._abort_if_unique_id_configured()
                    data: dict[str, Any] = {CONF_ADDRESS: address}
                    if aes_key:
                        data[CONF_AES_KEY] = aes_key
                    return self.async_create_entry(
                        title=f"Solar of Things BLE {address[-5:]}",
                        data=data,
                    )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ADDRESS,
                    default=(user_input or {}).get(CONF_ADDRESS, suggested_address),
                ): cv.string,
                vol.Optional(
                    CONF_AES_KEY,
                    default=(user_input or {}).get(CONF_AES_KEY, ""),
                ): cv.string,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
