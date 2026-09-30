# Smart Weather System + Raspberry Pi Connect

Raspberry Pi 1 Model B+ weather station using a BME280 over I2C.

Features: temperature, humidity, pressure, approximate altitude, live Raspberry Pi Connect terminal dashboard, optional Flask web dashboard, 5-second refresh.

## Setup

1. Enable I2C with `sudo raspi-config` -> Interface Options -> I2C.
2. Check the sensor with `i2cdetect -y 1`. BME280 is commonly `0x76`; some boards use `0x77`.
3. Install packages:

    sudo apt update
    sudo apt install -y python3-flask python3-pip i2c-tools
    python3 -m pip install --break-system-packages smbus2 RPi.bme280

4. Install Raspberry Pi Connect:

    sudo apt install rpi-connect-lite
    rpi-connect on
    rpi-connect signin
    rpi-connect status

5. Put this project at `/home/pi/smart_weather_system` and run:

    chmod +x connect-start.sh
    cd ~/smart_weather_system
    ./connect-start.sh

Press Ctrl+C to stop the live dashboard.

## Local web dashboard

Run `python3 app.py`, then open `http://PI-IP:5000` on your LAN.
Raspberry Pi Connect does not directly publish arbitrary Flask ports.

## Optional systemd service

    sudo cp smart-weather-connect.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now smart-weather-connect.service

Check with `systemctl status smart-weather-connect.service`.
