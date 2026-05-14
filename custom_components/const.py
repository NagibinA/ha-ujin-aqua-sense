"""Константы для Ujin Aqua-Sense BLE интеграции."""

DOMAIN = "ujin_aqua_sense"
MANUFACTURER_ID = 0xFFFF
DEVICE_NAME = "Ujin Aqua-Sense"

# Статусы событий
STATUS_LEAK = 0x02      # протечка (leak)
STATUS_INPUT = 0x04     # внешний датчик протечки (input)
STATUS_PRESS = 0x01     # нажатие кнопки
STATUS_LONG_PRESS = 0x20    # долгое нажатие
STATUS_VERY_LONG_PRESS = 0x40  # очень долгое нажатие

# Человекочитаемые названия
STATUS_NAMES = {
    STATUS_PRESS: "Нажатие кнопки",
    STATUS_LEAK: "Протечка",
    STATUS_INPUT: "Внешний датчик протечки",
    STATUS_LONG_PRESS: "Долгое нажатие",
    STATUS_VERY_LONG_PRESS: "Очень долгое нажатие",
}

# События для автоматизаций
EVENT_LEAK = f"{DOMAIN}_leak"
EVENT_INPUT_LEAK = f"{DOMAIN}_input_leak"
EVENT_BUTTON = f"{DOMAIN}_button"