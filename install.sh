#!/bin/bash
set -euo pipefail

APP="/opt/smart-weather-system"
SRC="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$APP"
cp "$SRC/weather_station.py" "$APP/"
cp "$SRC/bme280_sensor.py" "$APP/"

apt-get update
apt-get install -y python3-tk i2c-tools python3-pip
python3 -m pip install --break-system-packages smbus2 RPi.bme280 RPi.GPIO

# Enable I2C for the BME280 sensor on Raspberry Pi OS.
if [ -f /boot/firmware/config.txt ]; then
    if grep -qE '^[#[:space:]]*dtparam=i2c_arm=' /boot/firmware/config.txt; then
        sed -i 's/^[#[:space:]]*dtparam=i2c_arm=.*/dtparam=i2c_arm=on/' /boot/firmware/config.txt
    else
        printf '\n# Smart Weather System\ndtparam=i2c_arm=on\n' >> /boot/firmware/config.txt
    fi
fi

chmod 755 "$APP"
chmod 644 "$APP/weather_station.py" "$APP/bme280_sensor.py"

DESKTOP_USER=""
if [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ]; then
    DESKTOP_USER="${SUDO_USER}"
else
    DESKTOP_USER="$(getent passwd | awk -F: '$3 >= 1000 && $3 < 60000 && $7 !~ /(nologin|false)$/ {print $1; exit}')"
fi

if [ -n "$DESKTOP_USER" ] && [ -d "/home/$DESKTOP_USER" ]; then
    DESKTOP_HOME="$(getent passwd "$DESKTOP_USER" | cut -d: -f6)"
    AUTOSTART_DIR="$DESKTOP_HOME/.config/autostart"
    mkdir -p "$AUTOSTART_DIR"

    cat > "$AUTOSTART_DIR/weather-station.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=RPi Weather Observatory
Comment=Full-screen Smart Weather System dashboard
Exec=/usr/bin/python3 $APP/weather_station.py
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

    chown -R "$DESKTOP_USER:$DESKTOP_USER" "$DESKTOP_HOME/.config"
    chmod 644 "$AUTOSTART_DIR/weather-station.desktop"
    echo "Weather dashboard will start automatically after graphical login."
else
    echo "No graphical desktop user was detected."
    echo "After logging in to the desktop, run: python3 $APP/weather_station.py"
fi

echo "Smart Weather System installation complete."
echo "Tkinter dashboard is ready for Raspberry Pi OS 13."
