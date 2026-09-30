#!/bin/bash
set -e
APP=/opt/smart-weather-system
mkdir -p "$APP"
cp -r ./* "$APP/"
apt-get update
apt-get install -y python3-flask python3-pip i2c-tools
if grep -q '^dtparam=i2c_arm=' /boot/firmware/config.txt 2>/dev/null; then sed -i 's/^dtparam=i2c_arm=.*/dtparam=i2c_arm=on/' /boot/firmware/config.txt; else printf '\ndtparam=i2c_arm=on\n' >> /boot/firmware/config.txt; fi
python3 -m pip install --break-system-packages smbus2 RPi.bme280
printf 'test\n' > "$APP/mode.conf"
cp "$APP/smart-weather.service" /etc/systemd/system/smart-weather.service
systemctl daemon-reload
systemctl enable --now smart-weather.service
