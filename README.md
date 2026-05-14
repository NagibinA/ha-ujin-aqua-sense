# Ujin Aqua-Sense BLE for Home Assistant

Custom integration for Ujin Aqua-Sense BLE water leak sensor.

## Features
- Battery level monitoring (%)
- External sensor detection (input)
- Built-in leak detection
- Events for automations

## Installation via HACS
1. Make sure HACS is installed
2. Go to HACS → Integrations
3. Click three dots → "Custom repositories"
4. Add: `https://github.com/NagibinA/ha-ujin-aqua-sense`
5. Category: "Integration"
6. Click "ADD"
7. Find "Ujin Aqua-Sense BLE" and click "DOWNLOAD"

## Manual Installation
1. Download `ujin_aqua_sense` folder from `custom_components`
2. Copy to `custom_components` folder in your Home Assistant
3. Restart Home Assistant

## Configuration
1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Find "Ujin Aqua-Sense BLE"
4. Enter your device MAC address (example: `01:00:5E:00:38:C8`)

## Automation Example
```yaml
automation:
  trigger:
    - platform: state
      entity_id: binary_sensor.ujin_aqua_sense_external_sensor
      to: "on"
  action:
    - service: notify.mobile_app_phone
      data:
        message: "Water leak detected!"