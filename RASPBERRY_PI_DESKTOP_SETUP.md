# Raspberry Pi Desktop Weather Station

The repository includes a full-screen Tkinter desktop dashboard in `weather_station.py`.

## Important

The main Raspberry Pi display **does not use Chromium**. The dashboard is a native Python/Tkinter application.

## Run without the BME280

On the Raspberry Pi:

```bash
sudo apt update
sudo apt install -y python3-tk

mkdir -p ~/weather-station
cp weather_station.py ~/weather-station/
cd ~/weather-station
python3 weather_station.py
```

TEST Mode requires no sensor.

## Automatic startup

Raspberry Pi OS desktop sessions can launch applications using a per-user `~/.config/autostart/` desktop entry. The project's installer creates this automatically. Raspberry Pi's current desktop documentation also uses desktop-session autostart for graphical applications. citeturn0search0

If you are setting it up manually:

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/weather-station.desktop
```

Put this in the file:

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

```sudo reboot```

After the graphical desktop logs in, the weather dashboard should open full-screen. No Chromium command is used.

## Existing Chromium autostart

If **your Pi already has a separate Chromium autostart entry**, this project does not need it. The project itself does not create one.

To find an existing Chromium autostart entry, you can check:

```bash
grep -Rni "chromium" ~/.config/autostart ~/.config/labwc 2>/dev/null
```

If that command shows a Chromium entry, remove or disable that separate entry. Do not remove the weather-station entry.

## Modes

### TEST MODE
- Requires no sensor.
- Generates simulated temperature, humidity, pressure, altitude and rain values.
- Draws temperature and pressure graphs.
- Tracks minimum and maximum temperature.

### LIVE MODE
- Reserved for the BME280.
- Until BME280 support is connected to the desktop app, it displays BME280 NOT CONNECTED.

The app has large built-in TEST MODE and LIVE MODE buttons for instant switching.

Other controls:
- RESET MIN / MAX resets temperature extremes.
- Esc exits fullscreen.

## Optional web dashboard

The original Flask web dashboard remains in the repository and can be used from another device on the network. It is separate from the native desktop display and is not required for the Pi's local screen.
