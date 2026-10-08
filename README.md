# RPi Weather Observatory

A lightweight Raspberry Pi 1 Model B+ weather station for a science exhibition.

## Hardware

- Raspberry Pi 1 Model B+
- BMP180: temperature + atmospheric pressure
- DHT22: humidity + temperature
- DS3231: real-time clock
- LM393 raindrop sensor: rain/dry
- Breadboard and jumper wires

## Wiring

| Module | Pin | Raspberry Pi |
|---|---|---|
| BMP180 | VCC | 3.3V, physical 1 |
| BMP180 | GND | GND, physical 6 |
| BMP180 | SDA | GPIO2/SDA, physical 3 |
| BMP180 | SCL | GPIO3/SCL, physical 5 |
| DHT22 | VCC | 3.3V |
| DHT22 | DATA | GPIO4, physical 7 |
| DHT22 | GND | GND |
| DS3231 | SDA | GPIO2/SDA, physical 3 |
| DS3231 | SCL | GPIO3/SCL, physical 5 |
| DS3231 | GND | GND |
| DS3231 | VCC | Use the voltage required by your exact module |
| Rain module | DO | GPIO17, physical 11 |
| Rain module | GND | GND |
| Rain module | VCC | 3.3V |

BMP180 and DS3231 share the I2C SDA/SCL bus.

**DS3231 warning:** common ZS-042 boards can include a charging circuit intended for rechargeable cells. Verify the exact board before fitting a non-rechargeable CR2032.

## Dashboard

The native Tkinter dashboard provides:

- TEST / LIVE modes
- Temperature
- Humidity
- Atmospheric pressure
- Approximate altitude
- Rain / dry status
- DS3231 date and time
- Temperature minimum / maximum
- Temperature, humidity and pressure history graphs
- Individual sensor error reporting
- Full-screen exhibition view
- Automatic graphical-login startup

It does not use Chromium, a web browser, React, Electron or Matplotlib.

## TEST mode

TEST mode works with no sensors connected. It generates realistic changing weather data so the exhibition dashboard can be demonstrated before hardware is attached.

## LIVE mode

LIVE mode reads:

- BMP180 over I2C address normally 0x77
- DHT22 on GPIO4
- DS3231 over I2C address 0x68
- Rain sensor DO on GPIO17

A missing sensor is reported instead of crashing the dashboard.

## Installation

From the repository directory:

```bash
sudo bash install.sh
sudo reboot
```

The installer enables I2C, installs the required Python packages, copies the dashboard and sensor drivers to `/opt/smart-weather-system`, and creates a desktop autostart entry.

## Check I2C

After reboot:

```bash
sudo i2cdetect -y 1
```

You should normally see the BMP180 at `77` and DS3231 at `68`.

## Manual run

```bash
python3 /opt/smart-weather-system/weather_station.py
```

Windowed development mode:

```bash
python3 /opt/smart-weather-system/weather_station.py --windowed
```

## Project files

- `weather_station.py` - native Tkinter dashboard
- `sensors/bmp180.py` - BMP180 I2C driver
- `sensors/dht22.py` - DHT22 driver
- `sensors/ds3231.py` - DS3231 I2C reader
- `sensors/rain_sensor.py` - GPIO17 rain detector
- `install.sh` - Raspberry Pi installation and autostart

## Portable pocket mode

The project can be used as a portable local weather station. It does not
need Wi-Fi or a desktop display to measure local conditions.

Use a suitable USB power bank to power the Raspberry Pi, keep the OLED visible,
and place the temperature/humidity sensor and rain sensor where air can reach
them. Keep the Pi and power bank protected from rain and moisture.

Start OLED-only portable mode with:

```bash
python3 /opt/smart-weather-system/portable_weather.py
```

The OLED shows temperature, humidity, pressure, rain status and time. This
mode runs without Tkinter/X/desktop display.

For the exhibition, the normal `weather_station.py` dashboard can still be
used when a larger screen is available.
