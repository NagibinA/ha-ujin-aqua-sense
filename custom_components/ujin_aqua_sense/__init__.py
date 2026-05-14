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

from .const import (
    DOMAIN,
    STATUS_PRESS,
    STATUS_LEAK,
    STATUS_INPUT,
    STATUS_LONG_PRESS,
    STATUS_VERY_LONG_PRESS,
    EVENT_LEAK,
    EVENT_INPUT_LEAK,
    EVENT_BUTTON,
)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Настройка интеграции из config entry."""
    
    hass.data.setdefault(DOMAIN, {})
    
    coordinator = UjinAquaSenseCoordinator(hass, entry.entry_id, entry.unique_id)
    
    # Регистрируем callback для BLE (без фильтра manufacturer_id)
    entry.async_on_unload(
        async_register_callback(
            hass,
            coordinator._handle_advertisement,
            None,
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
            # Проверяем MAC-адрес
            if service_info.address.lower() != self.address:
                return
            
            _LOGGER.debug("Получен пакет от %s", service_info.address)
            _LOGGER.debug("Manufacturer data: %s", service_info.manufacturer_data)
            _LOGGER.debug("Service data: %s", service_info.service_data)
            
            # Получаем данные
            raw_data = None
            if service_info.manufacturer_data:
                for key, data in service_info.manufacturer_data.items():
                    raw_data = data
                    _LOGGER.debug("Получены manufacturer_data с key=%s", key)
                    break
            elif service_info.service_data:
                for key, data in service_info.service_data.items():
                    raw_data = data
                    _LOGGER.debug("Получены service_data с key=%s", key)
                    break
            
            if not raw_data:
                _LOGGER.warning("Нет данных от %s", self.address)
                return
            
            _LOGGER.debug("Raw data (hex): %s", raw_data.hex())
            
            parsed_data = self._parse_packet(raw_data)
            
            if parsed_data:
                _LOGGER.debug("Распарсенные данные: %s", parsed_data)
                self.last_data = parsed_data
                
                for listener in self.listeners:
                    listener(parsed_data)
                
                self._fire_events(parsed_data)
            else:
                _LOGGER.warning("Не удалось распарсить пакет от %s", self.address)
                
        except Exception as e:
            _LOGGER.error("Ошибка обработки BLE-пакета: %s", e, exc_info=True)
    
    def _parse_packet(self, raw_data: bytes) -> dict:
        """
        Парсинг пакета Ujin Aqua-Sense (LD-S).
        
        Формат: 05 09 4C 44 2D 53 08 FF FF FF 03 07 50 04 73
        - байт 12 (индекс 12) = battery (0-100)
        - байт 13 (индекс 13) = status
        """
        if len(raw_data) < 14:
            _LOGGER.debug("Пакет слишком короткий: %d байт", len(raw_data))
            return None
        
        battery = raw_data[12]
        status_byte = raw_data[13]
        
        # Определяем тип события
        event_type = None
        if status_byte & STATUS_INPUT:
            event_type = "input_leak"
        elif status_byte & STATUS_LEAK:
            event_type = "leak"
        elif status_byte & STATUS_VERY_LONG_PRESS:
            event_type = "very_long_press"
        elif status_byte & STATUS_LONG_PRESS:
            event_type = "long_press"
        elif status_byte & STATUS_PRESS:
            event_type = "press"
        
        result = {
            "battery": battery,
            "status_byte": status_byte,
            "event_type": event_type,
            "is_leak": bool(status_byte & STATUS_LEAK),
            "is_input_leak": bool(status_byte & STATUS_INPUT),
            "is_press": bool(status_byte & STATUS_PRESS),
            "is_long_press": bool(status_byte & STATUS_LONG_PRESS),
            "is_very_long_press": bool(status_byte & STATUS_VERY_LONG_PRESS),
        }
        
        _LOGGER.debug("Парсинг: батарея=%d%%, статус=0x%02X, событие=%s",
                      battery, status_byte, event_type)
        
        return result
    
    def _fire_events(self, data: dict) -> None:
        """Генерация событий для автоматизаций."""
        if data["is_leak"]:
            self.hass.bus.async_fire(EVENT_LEAK, {
                "device_id": self.address,
                "battery": data["battery"],
            })
        
        if data["is_input_leak"]:
            self.hass.bus.async_fire(EVENT_INPUT_LEAK, {
                "device_id": self.address,
                "battery": data["battery"],
            })
        
        if data["is_press"] or data["is_long_press"] or data["is_very_long_press"]:
            self.hass.bus.async_fire(EVENT_BUTTON, {
                "device_id": self.address,
                "battery": data["battery"],
                "type": data["event_type"],
            })
    
    def async_add_listener(self, update_callback):
        """Добавление слушателя обновлений."""
        self.listeners.append(update_callback)
        return lambda: self.listeners.remove(update_callback)