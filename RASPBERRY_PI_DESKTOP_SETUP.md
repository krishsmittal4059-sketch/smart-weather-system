# Raspberry Pi Desktop Weather Station

The repository contains a full-screen Tkinter dashboard in `weather_station.py`.

## Important

The weather system **does not use Chromium** or any web browser.

## Run manually

```bash
sudo apt update
sudo apt install -y python3-tk

python3 weather_station.py
```

TEST Mode requires no sensor.

## Automatic startup

The installer creates a per-user desktop autostart entry.

If you need to create it manually:

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/weather-station.desktop
```

Use:

```ini
[Desktop Entry]
Type=Application
Name=Smart Weather Station
Comment=Full-screen Smart Weather System desktop dashboard
Exec=/usr/bin/python3 /home/pi/weather-station/weather_station.py
Terminal=false
X-GNOME-Autostart-enabled=true
```

If your username is not `pi`, replace `/home/pi/` with your actual home directory. Check with:

```bash
whoami
```

Then reboot:

```bash
sudo reboot
```

After the graphical desktop logs in, the weather dashboard opens full-screen.

## If Chromium still starts

The Smart Weather System itself does not start Chromium.

To find an old Chromium autostart entry:

```bash
grep -Rni "chromium" ~/.config/autostart ~/.config/labwc 2>/dev/null
```

If you find a Chromium entry, it belongs to the Pi's existing desktop configuration, not this project. Disable that entry if you do not want Chromium to start.

## Modes

### TEST MODE
- No sensor required.
- Simulated temperature, humidity, pressure, altitude and rain.
- Temperature and pressure graphs.
- Minimum and maximum temperature.

### LIVE MODE
- Reserved for the BME280.
- Until BME280 support is connected to the desktop app, it shows BME280 NOT CONNECTED.

Other controls:
- RESET MIN / MAX
- Esc exits fullscreen
