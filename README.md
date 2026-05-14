# Ujin Aqua-Sense BLE для Home Assistant

Кастомная интеграция для датчика протечки воды **Ujin Aqua-Sense BLE**.

## Возможности

- 📊 Отображение уровня заряда батареи (в процентах)
- 💧 Детекция протечки через встроенный датчик (на корпусе)
- 🔌 Детекция протечки через внешний датчик (input/клеммы)
- 🔘 Определение нажатий кнопки (обычное, долгое, очень долгое)
- 📡 Генерация событий для автоматизаций
- 🚀 Работает через Bluetooth Low Energy (BLE)
- 🔍 Автоматическое обнаружение датчиков

## Установка через HACS (рекомендуется)

1. Убедитесь, что HACS установлен в вашем Home Assistant
2. Перейдите в **HACS** → **Интеграции**
3. Нажмите на три точки в правом верхнем углу → **"Пользовательские репозитории"**
4. Добавьте ссылку: `https://github.com/NagibinA/ha-ujin-aqua-sense`
5. Выберите категорию: **"Интеграция"**
6. Нажмите **"ДОБАВИТЬ"**
7. Найдите интеграцию **"Ujin Aqua-Sense BLE"** и нажмите **"СКАЧАТЬ"**
8. Перезапустите Home Assistant

## Ручная установка

1. Скачайте папку `ujin_aqua_sense` из `custom_components` этого репозитория
2. Скопируйте её в папку `custom_components` вашего Home Assistant
3. Перезапустите Home Assistant


## Автоматическое обнаружение

Интеграция поддерживает автоматическое обнаружение датчиков **Ujin Aqua-Sense BLE** в Bluetooth-эфире.

### Как это работает:

1. Датчик при пробуждении отправляет BLE-пакеты с именем `LD-S`
2. Home Assistant автоматически обнаруживает новый датчик
3. В разделе **"Устройства и сервисы"** появляется уведомление
4. Нажмите **"Подтвердить"** — датчик добавится автоматически

### Что нужно для автообнаружения:

- Bluetooth-адаптер на устройстве с Home Assistant
- Или Bluetooth-прокси на ESP32 (рекомендуется для большой площади)
- Датчик должен быть в зоне действия Bluetooth

> **Примечание:** При первом добавлении может потребоваться несколько минут для обнаружения. Нажмите кнопку на датчике, чтобы он отправил пакет принудительно.

## Настройка

### Способ 1: Автоматический (рекомендуется)

1. Дождитесь уведомления об обнаружении нового устройства
2. Нажмите **"Подтвердить"**
3. Датчик автоматически добавится

### Способ 2: Ручной

1. Перейдите в **Настройки** → **Устройства и сервисы**
2. Нажмите **"Добавить интеграцию"**
3. Найдите **"Ujin Aqua-Sense BLE"**
4. Выберите устройство из списка или введите MAC-адрес вручную

> **Где взять MAC-адрес?**
> - В Home Assistant: Настройки → Bluetooth → Посмотреть доступные устройства
> - Или используйте приложение для сканирования BLE на телефоне

## Сущности (Entities)

После настройки у вас появятся следующие сущности:

| Тип | Название | Описание |
|-----|----------|----------|
| Сенсор | `sensor.ujin_aqua_sense_battery` | Уровень заряда батареи (0-100%) |
| Бинарный сенсор | `binary_sensor.ujin_aqua_sense_protechka` | Встроенный датчик протечки |
| Бинарный сенсор | `binary_sensor.ujin_aqua_sense_vneshniy_datchik` | Внешний датчик протечки |
| Бинарный сенсор | `binary_sensor.ujin_aqua_sense_nazhatie` | Обычное нажатие кнопки |
| Бинарный сенсор | `binary_sensor.ujin_aqua_sense_dolgoe_nazhatie` | Долгое нажатие кнопки |
| Бинарный сенсор | `binary_sensor.ujin_aqua_sense_ochen_dolgoe_nazhatie` | Очень долгое нажатие кнопки |

## События для автоматизаций

Интеграция генерирует следующие события:

| Событие | Описание | Данные в событии |
|---------|----------|------------------|
| `ujin_aqua_sense_leak` | Обнаружена протечка на корпусе | `device_id`, `battery` |
| `ujin_aqua_sense_input_leak` | Сработал внешний датчик | `device_id`, `battery` |
| `ujin_aqua_sense_button` | Нажата кнопка на датчике | `device_id`, `battery`, `type` |

### Типы нажатий кнопки (`type`)

- `press` — обычное нажатие
- `long_press` — долгое нажатие
- `very_long_press` — очень долгое нажатие

## Примеры автоматизаций

### 1. Уведомление при протечке (через бинарный сенсор)

```yaml
automation:
  - alias: "Уведомление о протечке"
    trigger:
      - platform: state
        entity_id: binary_sensor.ujin_aqua_sense_protechka
        to: "on"
    action:
      - service: notify.mobile_app_phone
        data:
          title: "🚨 ПРОТЕЧКА!"
          message: "Обнаружена вода на корпусе датчика"
```

### 2. Уведомление от внешнего датчика (через событие)

```yaml
automation:
  - alias: "Внешний датчик сработал"
    trigger:
      - platform: event
        event_type: ujin_aqua_sense_input_leak
    action:
      - service: notify.mobile_app_phone
        data:
          title: "⚠️ ВНИМАНИЕ"
          message: "Сработал внешний датчик протечки"
```

### 3. Управление светом по кнопке

```yaml
automation:
  - alias: "Кнопка датчика - управление светом"
    trigger:
      - platform: event
        event_type: ujin_aqua_sense_button
    action:
      - service: light.toggle
        target:
          entity_id: light.living_room
```

### 4. Оповещение о низком заряде батареи

```yaml
automation:
  - alias: "Низкий заряд батареи"
    trigger:
      - platform: numeric_state
        entity_id: sensor.ujin_aqua_sense_battery
        below: 20
    action:
      - service: notify.mobile_app_phone
        data:
          title: "🔋 НИЗКИЙ ЗАРЯД"
          message: "Батарея датчика протечки разряжена ({{ states('sensor.ujin_aqua_sense_battery') }}%)"
```

### 5. Отключение воды при протечке

```yaml
automation:
  - alias: "Аварийное отключение воды"
    trigger:
      - platform: state
        entity_id: 
          - binary_sensor.ujin_aqua_sense_protechka
          - binary_sensor.ujin_aqua_sense_vneshniy_datchik
        to: "on"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.water_valve
      - service: notify.mobile_app_phone
        data:
          title: "🚰 ВОДА ОТКЛЮЧЕНА"
          message: "Обнаружена протечка, подача воды перекрыта"
```

## Отладка и логи

Если что-то не работает, включите отладку в `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.ujin_aqua_sense: debug
```

Логи можно посмотреть в **Настройки** → **Система** → **Логи**.

## Проверка событий в реальном времени

1. Перейдите в **Разработчик инструментов** → **События**
2. В поле "Подписаться на событие" введите `ujin_aqua_sense_*`
3. Нажмите **"Подписаться"**
4. Нажмите кнопку на датчике — вы увидите событие

## Требования

- Home Assistant версии **2024.1.0** или выше
- Bluetooth-адаптер на устройстве с Home Assistant
- Или Bluetooth-прокси на ESP32

## Поддержка

Если вы нашли ошибку или есть предложения по улучшению:

- Создайте [Issue на GitHub](https://github.com/NagibinA/ha-ujin-aqua-sense/issues)

## Лицензия

MIT License

---
⭐ Не забудьте поставить звезду репозиторию, если интеграция вам помогла!

## Автор

[NagibinA](https://github.com/NagibinA)
