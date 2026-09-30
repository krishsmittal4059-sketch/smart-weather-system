# Smart Weather System

Raspberry Pi 1 Model B+ + BME280 weather station.

## Modes
- TEST MODE: simulated readings for exhibition testing.
- LIVE MODE: real BME280 readings over I2C.

## Hardware
BME280 I2C:
- VCC -> 3.3V
- GND -> GND
- SDA -> GPIO 2 / SDA
- SCL -> GPIO 3 / SCL

## Automatic setup
1. Write Raspberry Pi OS 13 (Trixie) 32-bit with Raspberry Pi Imager.
2. Configure the normal user and network in Imager.
3. Copy pi-boot/user-data and pi-boot/meta-data to the SD card boot partition.
4. Copy the project files into a folder named weather-system on that same boot partition.
5. Insert the card and power on.

The first boot installs dependencies, enables I2C, installs the app and starts it automatically. No commands are required on the Pi.

Open http://PI-IP:5000 on your network.
