# Smart Weather System

Raspberry Pi 1 Model B+ + BME280 weather station for a science exhibition.

## Main display

The Raspberry Pi uses the native **Tkinter Smart Weather Station** application.

- No Chromium required
- No web browser required
- Starts automatically after graphical login
- Full-screen dashboard
- TEST Mode works without a sensor
- LIVE Mode is reserved for the BME280
- Large TEST MODE / LIVE MODE buttons
- Temperature and pressure graphs
- Temperature minimum/maximum
- Rain indicator (simulated in TEST Mode; a separate rain sensor is required for real rain detection)

## Hardware

BME280 I2C breakout:
- VCC -> 3.3V
- GND -> GND
- SDA -> GPIO 2 / SDA
- SCL -> GPIO 3 / SCL

Do not connect a 3.3V BME280 module to 5V logic.

## Installation

1. Use Raspberry Pi Imager to write the appropriate Raspberry Pi OS image for the Pi 1 B+.
2. Configure the normal Raspberry Pi user and graphical desktop.
3. Copy `pi-boot/user-data` and `pi-boot/meta-data` to the SD card boot partition.
4. Copy the repository contents into a folder named `weather-system` on that boot partition.
5. Insert the SD card and power on.
6. The first-boot installer installs Tkinter and configures the desktop to launch `weather_station.py` automatically.
7. The weather dashboard starts full-screen after graphical login.

The application starts in Test Mode so it can be demonstrated before the BME280 is connected.

## Manual setup

If you already cloned the repository:

```bash
sudo apt update
sudo apt install -y python3-tk
python3 weather_station.py
```

For automatic startup, see `RASPBERRY_PI_DESKTOP_SETUP.md`.

## Project layout

- `weather_station.py` - native full-screen Tkinter dashboard
- `install.sh` - first-boot installer and desktop autostart setup
- `pi-boot/` - first-boot files
- `README.md` - project documentation
- `RASPBERRY_PI_DESKTOP_SETUP.md` - desktop setup instructions
