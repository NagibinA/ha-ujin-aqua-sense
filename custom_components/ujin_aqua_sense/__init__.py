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

from .const import DOMAIN

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Настройка интеграции из config entry."""
    
    hass.data.setdefault(DOMAIN, {})
    
    coordinator = UjinAquaSenseCoordinator(hass, entry.entry_id, entry.unique_id)
    
    entry.async_on_unload(
        async_register_callback(
            hass,
            coordinator._handle_advertisement,
            {"manufacturer_id": 0xFFFF},
            BluetoothScanningMode.PASSIVE,
        )
    )
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.unique_id)},
        name="Ujin Aqua-Sense",
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
        self.address = address.lower()
        self.last_data = {}
        self.listeners = []
    
    def _handle_advertisement(
        self, service_info: BluetoothServiceInfoBleak, change
    ) -> None:
        """Обработка входящего BLE-пакета."""
        try:
            if service_info.address.lower() != self.address:
                return
            
            _LOGGER.debug("Получен пакет от %s", service_info.address)
            
            if not service_info.manufacturer_data:
                _LOGGER.debug("Нет manufacturer_data")
                return
            
            if 0xFFFF not in service_info.manufacturer_data:
                _LOGGER.debug("Нет manufacturer_id 0xFFFF")
                return
            
            raw_data = service_info.manufacturer_data[0xFFFF]
            _LOGGER.debug("Raw data (hex): %s", raw_data.hex())
            
            parsed_data = self._parse_packet(raw_data)
            
            if parsed_data:
                _LOGGER.debug("Распарсенные данные: %s", parsed_data)
                self.last_data = parsed_data
                
                for listener in self.listeners:
                    listener(parsed_data)
                
                self._fire_events(parsed_data)
            else:
                _LOGGER.warning("Не удалось распарсить пакет")
                
        except Exception as e:
            _LOGGER.error("Ошибка обработки BLE-пакета: %s", e, exc_info=True)
    
    def _parse_packet(self, raw_data: bytes) -> dict:
        """
        Парсинг пакета Ujin Aqua-Sense (LD-S).
        
        В manufacturer_data приходят данные, начиная с initial:
        Байт 0-1: initial (2 байта, little-endian, всегда 0x0307)
        Байт 2:   battery (0-100)
        Байт 3:   status
        Байт 4:   counter (опционально)
        """
        if len(raw_data) < 4:
            _LOGGER.debug("Пакет слишком короткий: %d байт", len(raw_data))
            return None
        
        battery = raw_data[2]
        status_byte = raw_data[3]
        
        if len(raw_data) >= 2:
            initial = int.from_bytes(raw_data[0:2], byteorder='little')
            _LOGGER.debug("initial=0x%04X, battery=%d%%, status=0x%02X", initial, battery, status_byte)
        
        result = {
            "battery": battery,
            "status_byte": status_byte,
            "is_leak": bool(status_byte & 0x02),
            "is_input_leak": bool(status_byte & 0x04),
            "is_press": bool(status_byte & 0x01),
            "is_long_press": bool(status_byte & 0x20),
            "is_very_long_press": bool(status_byte & 0x40),
        }
        
        return result
    
    def _fire_events(self, data: dict) -> None:
        """Генерация событий для автоматизаций."""
        if data["is_leak"]:
            self.hass.bus.async_fire(f"{DOMAIN}_leak", {
                "device_id": self.address,
                "battery": data["battery"],
            })
        
        if data["is_input_leak"]:
            self.hass.bus.async_fire(f"{DOMAIN}_input_leak", {
                "device_id": self.address,
                "battery": data["battery"],
            })
        
        if data["is_press"] or data["is_long_press"] or data["is_very_long_press"]:
            event_type = "press"
            if data["is_very_long_press"]:
                event_type = "very_long_press"
            elif data["is_long_press"]:
                event_type = "long_press"
            
            self.hass.bus.async_fire(f"{DOMAIN}_button", {
                "device_id": self.address,
                "battery": data["battery"],
                "type": event_type,
            })
    
    def async_add_listener(self, update_callback):
        """Добавление слушателя обновлений."""
        self.listeners.append(update_callback)
        return lambda: self.listeners.remove(update_callback)