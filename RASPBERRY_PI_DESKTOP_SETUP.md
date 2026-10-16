# Raspberry Pi Desktop Weather Station

The repository contains the original full-screen Tkinter dashboard in weather_station.py. The current Arduino setup uses a DHT22 temperature/humidity sensor and an LM393 rain sensor; the BMP180 has been removed.

## Run manually

Install the dependencies:

    sudo apt update
    sudo apt install -y python3-tk python3-serial

From the repository directory, run:

    python3 weather_station.py

TEST MODE requires no sensor. Click LIVE MODE to read data from the Arduino UNO over USB. Close Arduino IDE Serial Monitor before starting LIVE mode.

## Dashboard controls

- LIVE MODE / TEST MODE switches between Arduino readings and simulated values.
- FULL SCREEN and WINDOWED change the dashboard size.
- RESET HISTORY clears the graphs and temperature min/max.
- EXIT closes the dashboard.
- F11 toggles full screen; Esc leaves full screen.

## Automatic startup

To create a per-user desktop autostart entry:

    mkdir -p ~/.config/autostart
    nano ~/.config/autostart/weather-station.desktop

Use the following, replacing /home/pi with your actual home directory if necessary:

    [Desktop Entry]
    Type=Application
    Name=Smart Weather Station
    Comment=Full-screen Smart Weather System desktop dashboard
    Exec=/usr/bin/python3 /home/pi/smart-weather-system/weather_station.py
    Terminal=false
    X-GNOME-Autostart-enabled=true

Find your home directory with:

    echo "$HOME"

Then log out and back in, or reboot:

    sudo reboot

## Troubleshooting

- Check the Arduino port with: ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
- Close Arduino IDE Serial Monitor before using LIVE mode.
- If serial permission is denied, run sudo usermod -aG dialout "$USER", then log out and back in.
- If no readings arrive, confirm the Arduino is running the repository's arduino/smart_weather_arduino.ino sketch at 9600 baud.
