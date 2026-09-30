# Smart Weather System

Raspberry Pi 1 Model B+ + BME280 weather station for a science exhibition.

## Features

- Automatic startup after Raspberry Pi OS setup
- Test Mode with simulated weather data
- Live Mode with BME280 temperature, humidity and pressure
- Automatic BME280 I2C address detection (0x76 / 0x77)
- Simple local web dashboard
- Designed for Raspberry Pi OS 13 32-bit / legacy-compatible images
- systemd service for automatic operation

## Hardware

BME280 I2C breakout:
- VCC -> 3.3V
- GND -> GND
- SDA -> GPIO 2 / SDA
- SCL -> GPIO 3 / SCL

Do not connect a 3.3V BME280 module to 5V logic.

## Installation

1. Use Raspberry Pi Imager to write the appropriate Raspberry Pi OS 13 32-bit image for the Pi 1 B+.
2. Configure the normal Raspberry Pi user and network in Imager.
3. Copy this repository's `pi-boot/user-data` and `pi-boot/meta-data` to the SD card boot partition.
4. Copy the repository contents into a folder named `weather-system` on that boot partition.
5. Insert the SD card and power on.
6. The first boot installs the application and starts it automatically.

The application normally starts in Test Mode so the exhibition can be demonstrated even before the BME280 is connected.

## Dashboard

Find the Pi's IP address from your network/router and open:

`http://PI-IP:5000`

Raspberry Pi Connect is separate from this dashboard. If Connect is enabled on the Pi, use its terminal/remote access normally; the weather dashboard still runs on port 5000.

## Project layout

- `app.py` - Flask web server
- `weather_data.py` - Test/Live sensor logic
- `templates/index.html` - dashboard
- `install.sh` - first-boot installer
- `smart-weather.service` - systemd service
- `pi-boot/` - first-boot cloud-init files
