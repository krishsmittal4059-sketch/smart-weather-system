#!/bin/bash
set -euo pipefail

APP="/opt/smart-weather-system"
SRC="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$APP/sensors"
cp "$SRC/weather_station.py" "$APP/"
cp -r "$SRC/sensors/." "$APP/sensors/"

apt-get update
apt-get install -y python3-tk python3-pip python3-smbus i2c-tools python3-rpi.gpio

python3 -m pip install --break-system-packages smbus2 Adafruit_DHT || \
python3 -m pip install --user smbus2 Adafruit_DHT

CONFIG="/boot/firmware/config.txt"
[ -f "$CONFIG" ] || CONFIG="/boot/config.txt"
if [ -f "$CONFIG" ]; then
    if grep -qE '^[#[:space:]]*dtparam=i2c_arm=' "$CONFIG"; then
        sed -i 's/^[#[:space:]]*dtparam=i2c_arm=.*/dtparam=i2c_arm=on/' "$CONFIG"
    else
        printf '\n# RPi Weather Observatory\ndtparam=i2c_arm=on\n' >> "$CONFIG"
    fi
fi

chmod 755 "$APP/weather_station.py"
chmod 755 "$APP/sensors"
chmod 644 "$APP/sensors/"*.py

DESKTOP_USER=""
if [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ]; then
    DESKTOP_USER="${SUDO_USER}"
else
    DESKTOP_USER="$(getent passwd | awk -F: '$3 >= 1000 && $3 < 60000 && $7 !~ /(nologin|false)$/ {print $1; exit}')"
fi

if [ -n "$DESKTOP_USER" ] && [ -d "/home/$DESKTOP_USER" ]; then
    HOME_DIR="$(getent passwd "$DESKTOP_USER" | cut -d: -f6)"
    AUTOSTART="$HOME_DIR/.config/autostart"
    mkdir -p "$AUTOSTART"
    cat > "$AUTOSTART/weather-station.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=RPi Weather Observatory
Comment=Native full-screen weather station dashboard
Exec=/usr/bin/python3 $APP/weather_station.py
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
    chown -R "$DESKTOP_USER:$DESKTOP_USER" "$AUTOSTART"
    chmod 644 "$AUTOSTART/weather-station.desktop"
fi

echo "RPi Weather Observatory installed."
echo "Reboot after installation, then the dashboard will start after graphical login."
echo "Test I2C with: sudo i2cdetect -y 1"
