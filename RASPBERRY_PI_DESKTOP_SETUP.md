# Raspberry Pi Desktop Weather Station

The repository now includes a full-screen Tkinter desktop dashboard in \`weather_station.py\`.

## Run without the BME280

On the Raspberry Pi:

sudo apt update
sudo apt install -y python3-tk

mkdir -p ~/weather-station
cp weather_station.py ~/weather-station/
cd ~/weather-station
python3 weather_station.py

## Modes

TEST MODE:
- Requires no sensor.
- Generates simulated temperature, humidity, pressure, altitude and rain values.
- Draws temperature and pressure graphs.
- Tracks minimum and maximum temperature.

LIVE MODE:
- Reserved for the BME280.
- Until BME280 support is connected, the app displays BME280 NOT CONNECTED.

The app has large built-in TEST MODE and LIVE MODE buttons for instant switching.

Other controls:
- RESET MIN / MAX resets temperature extremes.
- Esc exits fullscreen.

## Automatic startup

Create the desktop autostart directory:

mkdir -p ~/.config/autostart

Create:

nano ~/.config/autostart/weather-station.desktop

Use:

[Desktop Entry]
Type=Application
Name=Weather Station Desktop
Exec=/usr/bin/python3 /home/pi/weather-station/weather_station.py
Terminal=false
X-GNOME-Autostart-enabled=true

If your username is not pi, replace /home/pi/ with your actual home directory. Check with:

whoami

## Existing web dashboard

The repository also contains the original Flask web dashboard. This desktop program is an additional Raspberry Pi local display and does not remove the existing web application.
