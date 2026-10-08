# RPi Weather Observatory

A lightweight Raspberry Pi 1 Model B+ weather station for a science exhibition.

## Final hardware

- Raspberry Pi 1 Model B+
- BMP180: temperature + atmospheric pressure
- DHT11 3-pin module: humidity + temperature
- DS3231: real-time clock
- LM393 raindrop sensor: rain/dry
- 1.3 inch 128x64 I2C OLED, commonly SH1106 at 0x3C
- 400-point breadboard and jumper wires
- Portable 5V power-bank/charger board and enclosure

## Wiring

| Module | Pin | Raspberry Pi |
|---|---|---|
| BMP180 | VCC | 3.3V, physical 1 |
| BME280 | GND | GND, physical 6 |
| BME280 | SDA | GPIO2/SDA, physical 3 |
| BME280 | SCL | GPIO3/SCL, physical 5 |
| DHT11 | VCC | 3.3V |
| DHT11 | DATA | GPIO4, physical 7 |
| DHT11 | GND | GND |
| DS3231 | SDA | GPIO2/SDA, physical 3 |
| DS3231 | SCL | GPIO3/SCL, physical 5 |
| DS3231 | GND | GND |
| DS3231 | VCC | Use the voltage required by your exact module |
| Rain module | DO | GPIO17, physical 11 |
| Rain module | GND | GND |
| Rain module | VCC | 3.3V |
| OLED | VCC/VDD | 3.3V, physical 1 |
| OLED | GND | GND, physical 6 |
| OLED | SDA | GPIO2/SDA, physical 3 |
| OLED | SCL | GPIO3/SCL, physical 5 |

BMP180, OLED and DS3231 share the I2C SDA/SCL bus. Typical addresses are:
- BMP180: 0x77
- DS3231: 0x68
- OLED: 0x3C

**DS3231 warning:** common ZS-042 boards can include a charging circuit intended for rechargeable cells. Verify the exact board before fitting a non-rechargeable CR2032.

## Dashboard

The native Tkinter dashboard provides:

- TEST / LIVE modes
- BMP180 temperature
- DHT11 humidity
- BMP180 atmospheric pressure
- Approximate altitude from pressure
- Rain / dry status
- DS3231 date and time
- Temperature minimum / maximum
- Temperature, humidity and pressure history graphs
- Individual sensor error reporting
- Full-screen exhibition view
- Automatic graphical-login startup
- Optional OLED status output

It does not use Chromium, a web browser, React, Electron or Matplotlib.

## TEST mode

TEST mode works with no sensors connected. It generates realistic changing weather data so the exhibition dashboard can be demonstrated before hardware is attached.

## LIVE mode

LIVE mode reads:

- BMP180 over I2C at 0x77
- DHT11 on GPIO4
- DS3231 over I2C address 0x68
- Rain sensor DO on GPIO17
- OLED over I2C, normally 0x3C

A missing sensor is reported instead of crashing the dashboard.

## Installation

From the repository directory:

```bash
sudo bash install.sh
sudo reboot
```

The installer enables I2C, installs the required Python packages, copies the dashboard, sensor drivers and portable mode to `/opt/smart-weather-system`, and creates a desktop autostart entry.

## Check I2C

After reboot:

```bash
sudo i2cdetect -y 1
```

With all I2C hardware connected, you will normally see `68`, `3c`, and either `76` or `77`.

## Manual dashboard

```bash
python3 /opt/smart-weather-system/weather_station.py
```

Windowed development mode:

```bash
python3 /opt/smart-weather-system/weather_station.py --windowed
```

## Portable OLED mode

For the portable enclosure, run without the desktop:

```bash
python3 /opt/smart-weather-system/portable_weather.py
```

The OLED shows temperature, humidity, pressure, rain status, time and mode. This mode does not need Wi-Fi or a desktop display.

Keep the Pi and power electronics protected from rain and moisture. The DHT11 and rain sensor need exposure to the surrounding air/water as appropriate.

## Project files

- `weather_station.py` - native Tkinter dashboard
- `portable_weather.py` - OLED-only portable mode
- `sensors/bme280.py` - BME280 I2C driver
- `sensors/dht11.py` - DHT11 driver
- `sensors/ds3231.py` - DS3231 I2C reader
- `sensors/rain_sensor.py` - GPIO17 rain detector
- `sensors/oled.py` - SH1106/SSD1306 OLED output
- `install.sh` - Raspberry Pi installation and autostart
