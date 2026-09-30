#!/bin/bash
set -euo pipefail

APP="/opt/smart-weather-system"
SRC="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$APP"
cp "$SRC/weather_station.py" "$APP/"

apt-get update
apt-get install -y python3-tk i2c-tools

# Enable I2C now so the BME280 can be added later.
if [ -f /boot/firmware/config.txt ]; then
    if grep -qE '^[#[:space:]]*dtparam=i2c_arm=' /boot/firmware/config.txt; then
        sed -i 's/^[#[:space:]]*dtparam=i2c_arm=.*/dtparam=i2c_arm=on/' /boot/firmware/config.txt
    else
        printf '\n# Smart Weather System\ndtparam=i2c_arm=on\n' >> /boot/firmware/config.txt
    fi
fi

chmod 755 "$APP"
chmod 644 "$APP/weather_station.py"

# Launch the native Tkinter dashboard automatically after graphical login.
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
Name=Smart Weather Station
Comment=Full-screen Smart Weather System desktop dashboard
Exec=/usr/bin/python3 $APP/weather_station.py
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

    chown -R "$DESKTOP_USER:$DESKTOP_USER" "$DESKTOP_HOME/.config"
    chmod 644 "$AUTOSTART_DIR/weather-station.desktop"

    echo "Desktop user: $DESKTOP_USER"
    echo "Weather dashboard will start automatically after graphical login."
else
    echo "No graphical desktop user was detected."
    echo "Run the desktop setup commands in RASPBERRY_PI_DESKTOP_SETUP.md after logging into the normal desktop user."
fi

echo "Smart Weather System installed."
echo "Native Tkinter dashboard: no Chromium required."
