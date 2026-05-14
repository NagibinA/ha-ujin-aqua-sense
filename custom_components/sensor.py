"""Сенсор батареи для Ujin Aqua-Sense."""

from homeassistant.components.sensor import SensorEntity
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
    """Настройка сенсора батареи."""
    coordinator: UjinAquaSenseCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([UjinAquaSenseBatterySensor(entry, coordinator)])

class UjinAquaSenseBatterySensor(SensorEntity):
    """Сенсор заряда батареи."""
    
    def __init__(self, entry: ConfigEntry, coordinator: UjinAquaSenseCoordinator):
        self.entry = entry
        self.coordinator = coordinator
        self._attr_name = "Ujin Aqua-Sense Батарея"
        self._attr_unique_id = f"{entry.unique_id}_battery"
        self._attr_device_class = "battery"
        self._attr_unit_of_measurement = "%"
        self._attr_icon = "mdi:battery"
        self._attr_native_value = None
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
        battery = data.get("battery")
        self._attr_native_value = battery
        
        if battery is not None:
            if battery >= 80:
                self._attr_icon = "mdi:battery-high"
            elif battery >= 50:
                self._attr_icon = "mdi:battery-medium"
            elif battery >= 20:
                self._attr_icon = "mdi:battery-low"
            else:
                self._attr_icon = "mdi:battery-alert"
        
        self.async_write_ha_state()