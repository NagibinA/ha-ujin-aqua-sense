"""Бинарные сенсоры для Ujin Aqua-Sense."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from . import UjinAquaSenseCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Настройка бинарных сенсоров."""
    coordinator: UjinAquaSenseCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        UjinAquaSenseInputLeakSensor(entry, coordinator),
        UjinAquaSenseLeakSensor(entry, coordinator),
    ])

class UjinAquaSenseInputLeakSensor(BinarySensorEntity):
    """
    Внешний датчик протечки (input).
    Срабатывает при замыкании контактов внешнего датчика.
    """
    
    def __init__(self, entry: ConfigEntry, coordinator: UjinAquaSenseCoordinator):
        self.entry = entry
        self.coordinator = coordinator
        self._attr_name = "Ujin Aqua-Sense Внешний датчик"
        self._attr_unique_id = f"{entry.unique_id}_input_leak"
        self._attr_device_class = "moisture"
        self._attr_icon = "mdi:water"
        self._attr_is_on = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name="Ujin Aqua-Sense",
        )
        self._unsubscribe = None
    
    async def async_added_to_hass(self):
        self._unsubscribe = self.coordinator.async_add_listener(self._update)
    
    async def async_will_remove_from_hass(self):
        if self._unsubscribe:
            self._unsubscribe()
    
    @callback
    def _update(self, data):
        self._attr_is_on = data.get("is_input_leak", False)
        
        if self._attr_is_on:
            self._attr_icon = "mdi:water-alert"
        else:
            self._attr_icon = "mdi:water"
        
        self.async_write_ha_state()


class UjinAquaSenseLeakSensor(BinarySensorEntity):
    """
    Встроенный датчик протечки (leak).
    Срабатывает при контакте с водой на корпусе датчика.
    """
    
    def __init__(self, entry: ConfigEntry, coordinator: UjinAquaSenseCoordinator):
        self.entry = entry
        self.coordinator = coordinator
        self._attr_name = "Ujin Aqua-Sense Протечка"
        self._attr_unique_id = f"{entry.unique_id}_leak"
        self._attr_device_class = "moisture"
        self._attr_icon = "mdi:water"
        self._attr_is_on = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name="Ujin Aqua-Sense",
        )
        self._unsubscribe = None
    
    async def async_added_to_hass(self):
        self._unsubscribe = self.coordinator.async_add_listener(self._update)
    
    async def async_will_remove_from_hass(self):
        if self._unsubscribe:
            self._unsubscribe()
    
    @callback
    def _update(self, data):
        self._attr_is_on = data.get("is_leak", False)
        
        if self._attr_is_on:
            self._attr_icon = "mdi:water-alert"
        else:
            self._attr_icon = "mdi:water"
        
        self.async_write_ha_state()