#!/bin/bash
set -euo pipefail

APP="/opt/smart-weather-system"
SRC="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$APP" "$APP/templates"
cp "$SRC/app.py" "$APP/"
cp "$SRC/weather_data.py" "$APP/"
cp "$SRC/weather_station.py" "$APP/"
cp "$SRC/requirements.txt" "$APP/"
cp "$SRC/templates/index.html" "$APP/templates/"
cp "$SRC/smart-weather.service" /etc/systemd/system/smart-weather.service

apt-get update
apt-get install -y python3-flask python3-smbus2 python3-tk i2c-tools python3-venv

if [ -f /boot/firmware/config.txt ]; then
    if grep -qE '^[#[:space:]]*dtparam=i2c_arm=' /boot/firmware/config.txt; then
        sed -i 's/^[#[:space:]]*dtparam=i2c_arm=.*/dtparam=i2c_arm=on/' /boot/firmware/config.txt
    else
        printf '\n# Smart Weather System\ndtparam=i2c_arm=on\n' >> /boot/firmware/config.txt
    fi
fi

python3 -m venv --system-site-packages "$APP/venv"
"$APP/venv/bin/python" -m pip install --upgrade pip
"$APP/venv/bin/python" -m pip install --no-cache-dir -r "$APP/requirements.txt"

printf 'test\n' > "$APP/mode.conf"
chown -R root:root "$APP"
chmod 755 "$APP"
chmod 644 "$APP"/*.py "$APP"/*.txt "$APP/templates/index.html"
chmod 644 /etc/systemd/system/smart-weather.service

# Configure the graphical desktop to launch the Tkinter dashboard.
# This does not install, launch, or require Chromium.
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
    echo "No graphical desktop user was detected; desktop autostart was not configured."
    echo "Run the desktop setup commands in RASPBERRY_PI_DESKTOP_SETUP.md after creating/logging into the normal user."
fi

systemctl daemon-reload
systemctl enable smart-weather.service
systemctl restart smart-weather.service

echo "Smart Weather System installed."
echo "Desktop dashboard: starts automatically without Chromium."
echo "Web dashboard (optional): http://<PI-IP>:5000"
