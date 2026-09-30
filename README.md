# Smart Weather System

Raspberry Pi 1 Model B+ + BME280 weather station for a science exhibition.

## Main display

The Raspberry Pi desktop uses the native **Tkinter Smart Weather Station** application.

- No Chromium required
- No web browser required for the local display
- Starts automatically after graphical login
- Full-screen dashboard
- TEST Mode works without a sensor
- LIVE Mode is reserved for the BME280
- Large built-in TEST MODE / LIVE MODE buttons
- Temperature and pressure graphs
- Temperature minimum/maximum
- Rain indicator (simulated in TEST Mode; a separate rain sensor is required for real rain detection)

The original Flask web dashboard remains available as an optional network dashboard on port 5000. It is not needed by the desktop display.

## Hardware

BME280 I2C breakout:
- VCC -> 3.3V
- GND -> GND
- SDA -> GPIO 2 / SDA
- SCL -> GPIO 3 / SCL

Do not connect a 3.3V BME280 module to 5V logic.

## Installation

1. Use Raspberry Pi Imager to write the appropriate Raspberry Pi OS 13 32-bit image for the Pi 1 B+.
2. Configure the normal Raspberry Pi user and graphical desktop in Imager.
3. Copy this repository's `pi-boot/user-data` and `pi-boot/meta-data` to the SD card boot partition.
4. Copy the repository contents into a folder named `weather-system` on that boot partition.
5. Insert the SD card and power on.
6. The first-boot installer installs Tkinter and configures the desktop to launch `weather_station.py` automatically.
7. The desktop weather dashboard starts full-screen after graphical login.

The application normally starts in Test Mode so the exhibition can be demonstrated even before the BME280 is connected.

## Manual desktop setup

If you already cloned the repository on the Pi:

```bash
sudo apt update
sudo apt install -y python3-tk
mkdir -p ~/weather-station
cp weather_station.py ~/weather-station/
python3 weather_station.py
```

For automatic startup, see `RASPBERRY_PI_DESKTOP_SETUP.md`.

## Optional web dashboard

The Flask web dashboard can still be used from another device on the network:

`http://PI-IP:5000`

Chromium is **not** required on the Pi for the main dashboard.

## Project layout

- `weather_station.py` - native full-screen Tkinter desktop dashboard
- `app.py` - optional Flask web server
- `weather_data.py` - Test/Live sensor logic for the web dashboard
- `templates/index.html` - optional web dashboard
- `install.sh` - first-boot installer and desktop autostart setup
- `smart-weather.service` - optional web dashboard systemd service
- `pi-boot/` - first-boot cloud-init files
