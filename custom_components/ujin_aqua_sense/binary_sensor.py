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
        UjinAquaSenseLeakSensor(entry, coordinator),
        UjinAquaSenseInputLeakSensor(entry, coordinator),
        UjinAquaSenseButtonPressSensor(entry, coordinator),
        UjinAquaSenseButtonLongPressSensor(entry, coordinator),
        UjinAquaSenseButtonVeryLongPressSensor(entry, coordinator),
    ])

class UjinAquaSenseLeakSensor(BinarySensorEntity):
    """Встроенный датчик протечки (на корпусе)."""
    
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
        self._attr_icon = "mdi:water-alert" if self._attr_is_on else "mdi:water"
        self.async_write_ha_state()

class UjinAquaSenseInputLeakSensor(BinarySensorEntity):
    """Внешний датчик протечки (input/клеммы)."""
    
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
        self._attr_icon = "mdi:water-alert" if self._attr_is_on else "mdi:water"
        self.async_write_ha_state()


class UjinAquaSenseButtonPressSensor(BinarySensorEntity):
    """Обычное нажатие кнопки (сбрасывается автоматически)."""
    
    def __init__(self, entry: ConfigEntry, coordinator: UjinAquaSenseCoordinator):
        self.entry = entry
        self.coordinator = coordinator
        self._attr_name = "Ujin Aqua-Sense Кнопка (нажатие)"
        self._attr_unique_id = f"{entry.unique_id}_button_press"
        self._attr_icon = "mdi:gesture-tap-button"
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
        was_on = self._attr_is_on
        self._attr_is_on = data.get("is_press", False)
        
        if self._attr_is_on and not was_on:
            self.async_write_ha_state()
            # Автоматически сбрасываем через 1 секунду
            self.hass.async_create_task(self._async_reset())
        else:
            self.async_write_ha_state()
    
    async def _async_reset(self):
        await self.hass.async_add_executor_job(lambda: None)  # небольшая задержка
        await self.hass.async_create_task(self._async_do_reset())
    
    async def _async_do_reset(self):
        self._attr_is_on = False
        self.async_write_ha_state()


class UjinAquaSenseButtonLongPressSensor(BinarySensorEntity):
    """Долгое нажатие кнопки (сбрасывается автоматически)."""
    
    def __init__(self, entry: ConfigEntry, coordinator: UjinAquaSenseCoordinator):
        self.entry = entry
        self.coordinator = coordinator
        self._attr_name = "Ujin Aqua-Sense Кнопка (долгое нажатие)"
        self._attr_unique_id = f"{entry.unique_id}_button_long_press"
        self._attr_icon = "mdi:gesture-tap-hold"
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
        was_on = self._attr_is_on
        self._attr_is_on = data.get("is_long_press", False)
        
        if self._attr_is_on and not was_on:
            self.async_write_ha_state()
            self.hass.async_create_task(self._async_reset())
        else:
            self.async_write_ha_state()
    
    async def _async_reset(self):
        self._attr_is_on = False
        self.async_write_ha_state()


class UjinAquaSenseButtonVeryLongPressSensor(BinarySensorEntity):
    """Очень долгое нажатие кнопки (сбрасывается автоматически)."""
    
    def __init__(self, entry: ConfigEntry, coordinator: UjinAquaSenseCoordinator):
        self.entry = entry
        self.coordinator = coordinator
        self._attr_name = "Ujin Aqua-Sense Кнопка (очень долгое нажатие)"
        self._attr_unique_id = f"{entry.unique_id}_button_very_long_press"
        self._attr_icon = "mdi:gesture-tap-hold"
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
        was_on = self._attr_is_on
        self._attr_is_on = data.get("is_very_long_press", False)
        
        if self._attr_is_on and not was_on:
            self.async_write_ha_state()
            self.hass.async_create_task(self._async_reset())
        else:
            self.async_write_ha_state()
    
    async def _async_reset(self):
        self._attr_is_on = False
        self.async_write_ha_state()