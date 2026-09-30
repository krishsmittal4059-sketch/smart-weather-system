#!/bin/bash
set -euo pipefail

APP="/opt/smart-weather-system"
SRC="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$APP" "$APP/templates"
cp "$SRC/app.py" "$APP/"
cp "$SRC/weather_data.py" "$APP/"
cp "$SRC/requirements.txt" "$APP/"
cp "$SRC/templates/index.html" "$APP/templates/"
cp "$SRC/smart-weather.service" /etc/systemd/system/smart-weather.service

apt-get update
apt-get install -y python3-flask python3-smbus2 i2c-tools python3-venv

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

systemctl daemon-reload
systemctl enable smart-weather.service
systemctl restart smart-weather.service

echo "Smart Weather System installed."
echo "Dashboard: http://<PI-IP>:5000"
