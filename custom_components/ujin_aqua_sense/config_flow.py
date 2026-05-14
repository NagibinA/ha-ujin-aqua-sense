"""Config flow for Ujin Aqua-Sense BLE integration."""

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

class UjinAquaSenseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow для Ujin Aqua-Sense."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_device: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovered_device = discovery_info
        # Показываем MAC в заголовке окна подтверждения
        self.context["title_placeholders"] = {
            "name": "Ujin Aqua-Sense",
            "mac": discovery_info.address,
        }
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"Ujin Aqua-Sense ({self._discovered_device.address})",
                data={"address": self._discovered_device.address},
            )

        self._set_confirm_only()
        # Показываем MAC в описании
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": "Ujin Aqua-Sense",
                "mac": self._discovered_device.address,
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device."""
        if user_input is not None:
            address = user_input["address"]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Ujin Aqua-Sense ({address})",
                data={"address": address},
            )

        # Поиск устройств LD-S
        current_addresses = self._async_current_ids()
        self._discovered_devices.clear()
        
        for discovery in async_discovered_service_info(self.hass):
            if discovery.address in current_addresses:
                continue
            if discovery.name and "LD-S" in discovery.name:
                self._discovered_devices[discovery.address] = discovery

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        # Формируем список с MAC адресами
        devices_list = {
            address: f"{discovery.name} [{address}]"
            for address, discovery in self._discovered_devices.items()
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("address"): vol.In(devices_list)
                }
            ),
        )