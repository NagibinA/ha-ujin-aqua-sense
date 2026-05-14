"""Настройка интеграции через UI."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.components import bluetooth

from .const import DOMAIN

class UjinAquaSenseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow для Ujin Aqua-Sense."""
    
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Первый шаг - ввод MAC адреса."""
        errors = {}
        
        if user_input is not None:
            address = user_input["address"].upper()
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Ujin Aqua-Sense",
                data={"address": address},
            )
        
        schema = vol.Schema({
            vol.Required("address"): str,
        })
        
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "example": "01:00:5E:00:38:C8"
            }
        )