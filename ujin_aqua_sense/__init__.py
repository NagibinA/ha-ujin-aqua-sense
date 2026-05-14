"""Инициализация Ujin Aqua-Sense BLE интеграции."""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.const import Platform
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, MANUFACTURER_ID

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Настройка интеграции из config entry."""
    
    hass.data.setdefault(DOMAIN, {})
    
    coordinator = UjinAquaSenseCoordinator(hass, entry.entry_id, entry.unique_id)
    
    # Регистрируем callback для BLE
    entry.async_on_unload(
        async_register_callback(
            hass,
            coordinator._handle_advertisement,
            {"manufacturer_id": MANUFACTURER_ID},
            BluetoothScanningMode.PASSIVE,
        )
    )
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Создаем device registry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.unique_id)},
        name=f"Ujin Aqua-Sense",
        manufacturer="Ujin",
        model="Aqua-Sense BLE",
    )
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Выгрузка интеграции."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class UjinAquaSenseCoordinator:
    """Координатор для обработки BLE-пакетов Ujin Aqua-Sense."""
    
    def __init__(self, hass: HomeAssistant, entry_id: str, address: str):
        self.hass = hass
        self.entry_id = entry_id
        self.address = address
        self.last_data = {}
        self.listeners = []
    
    def _handle_advertisement(
        self, service_info: BluetoothServiceInfoBleak, change
    ) -> None:
        """Обработка входящего BLE-пакета."""
        try:
            # Проверяем, что пакет от нашего устройства
            if service_info.address.lower() != self.address.lower():
                return
            
            # Проверяем наличие manufacturer_data
            if MANUFACTURER_ID not in service_info.manufacturer_data:
                return
            
            raw_data = service_info.manufacturer_data[MANUFACTURER_ID]
            
            # Парсим пакет
            parsed_data = self._parse_packet(raw_data)
            
            if parsed_data:
                self.last_data = parsed_data
                
                # Уведомляем подписчиков
                for listener in self.listeners:
                    listener(parsed_data)
                
                # Генерируем события
                self._fire_events(parsed_data)
                
        except Exception as e:
            _LOGGER.error("Ошибка обработки BLE-пакета: %s", e)
    
    def _parse_packet(self, raw_data: bytes) -> dict:
        """
        Парсинг пакета Ujin Aqua-Sense.
        
        Пакет: 05 09 4C 44 2D 53 08 FF FF FF 03 07 50 04 73
        - байт 12 (индекс 12) = battery (0x50 = 80%)
        - байт 13 (индекс 13) = status (0x04 = input)
        """
        if len(raw_data) < 14:
            return None
        
        battery = raw_data[12]
        status_byte = raw_data[13]
        
        # Определяем основное событие
        events = []
        if status_byte & STATUS_INPUT:
            events.append("input_leak")
        if status_byte & STATUS_LEAK:
            events.append("leak")
        if status_byte & STATUS_PRESS:
            events.append("press")
        if status_byte & STATUS_LONG_PRESS:
            events.append("long_press")
        if status_byte & STATUS_VERY_LONG_PRESS:
            events.append("very_long_press")
        
        # Основной статус (приоритет: input_leak > leak > press)
        if status_byte & STATUS_INPUT:
            main_event = "input_leak"
        elif status_byte & STATUS_LEAK:
            main_event = "leak"
        elif status_byte & STATUS_PRESS:
            main_event = "press"
        elif status_byte & STATUS_LONG_PRESS:
            main_event = "long_press"
        elif status_byte & STATUS_VERY_LONG_PRESS:
            main_event = "very_long_press"
        else:
            main_event = "none"
        
        result = {
            "battery": battery,
            "status_byte": status_byte,
            "main_event": main_event,
            "events": events,
            "is_leak": bool(status_byte & STATUS_LEAK),
            "is_input_leak": bool(status_byte & STATUS_INPUT),
        }
        
        _LOGGER.debug(
            "Пакет от %s: батарея=%d%%, статус=0x%02X, события=%s",
            self.address, battery, status_byte, events
        )
        
        return result
    
    def _fire_events(self, data: dict) -> None:
        """Генерация событий для автоматизаций."""
        status_byte = data["status_byte"]
        
        if status_byte & STATUS_INPUT:
            self.hass.bus.async_fire(EVENT_INPUT_LEAK, {
                "device_id": self.address,
                "battery": data["battery"],
            })
        
        if status_byte & STATUS_LEAK:
            self.hass.bus.async_fire(EVENT_LEAK, {
                "device_id": self.address,
                "battery": data["battery"],
            })
        
        if status_byte & (STATUS_PRESS | STATUS_LONG_PRESS | STATUS_VERY_LONG_PRESS):
            self.hass.bus.async_fire(EVENT_BUTTON, {
                "device_id": self.address,
                "battery": data["battery"],
                "type": data["main_event"],
            })
    
    def async_add_listener(self, update_callback):
        """Добавление слушателя обновлений."""
        self.listeners.append(update_callback)
        return lambda: self.listeners.remove(update_callback)