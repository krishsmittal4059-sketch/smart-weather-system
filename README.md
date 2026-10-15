# Smart Weather Observatory

A Raspberry Pi 1 Model B+ science-exhibition weather dashboard. The Arduino UNO reads all three sensors and sends measurements to the Pi over USB serial. The Pi displays readings and graphs in a Tkinter dashboard.

## Hardware

- Raspberry Pi 1 Model B+ running Raspberry Pi OS
- Arduino UNO and USB data cable to the Pi
- BMP180 pressure/temperature breakout
- DHT22 3-pin module (temperature/humidity)
- LM393 rain comparator board and matching rain plate
- Breadboard and jumper wires

## Important safety check before wiring

The DHT22 module and LM393 comparator board were previously reported to become hot immediately after power-on. **Keep the Pi and Arduino unplugged and do not power either hot module again until its VCC/GND labels and wiring have been checked.** A module getting hot can indicate reversed power, a short, incompatible voltage or a damaged board. Do not assume the wiring is safe just because the BMP180 stayed cool. If uncertain, compare the exact board labels with its documentation or ask a knowledgeable adult/teacher to inspect it.

## Wiring

### BMP180 → Arduino UNO (I2C)

| BMP180 breakout label | Arduino UNO |
|---|---|
| VIN/VCC | 3.3V only if the breakout is specified for 3.3V; follow its printed rating |
| GND | GND |
| SDA | A4 (SDA) |
| SCL | A5 (SCL) |

The bare BMP180 chip is not a 5V part. Some breakout boards include a regulator/level shifting and some do not, so check the exact board before connecting power. Do not guess from wire colours.

### DHT22 3-pin module → Arduino UNO

Use the actual printed `+`/`VCC`, `OUT`/`DATA`, and `-`/`GND` labels on the module; pin order varies by module.

| DHT22 module label | Arduino UNO |
|---|---|
| VCC/+ | Supply voltage supported by the module |
| DATA/OUT | D2 |
| GND/- | GND |

### LM393 rain module → Arduino UNO

| Rain comparator label | Arduino UNO |
|---|---|
| VCC | Only the voltage specified for that exact board |
| GND | GND |
| DO | D3 |
| AO | Leave disconnected (not used) |

Connect the separate rain plate to its matching comparator-board connector. Many LM393 boards output LOW when wet, but the behaviour can vary; confirm it during a safe test.

### Arduino UNO → Raspberry Pi

Connect the UNO to the Pi with a USB **data** cable. Do not connect the UNO's 5V pin or its 5V signal pins directly to Raspberry Pi GPIO.

## Arduino setup

1. Open Arduino IDE on a computer and select **Arduino UNO**.
2. In Library Manager install:
   - **Adafruit BMP085 Library** (supports BMP180)
   - **DHT sensor library by Adafruit**
   - **Adafruit Unified Sensor**
3. Open [arduino/smart_weather_arduino.ino](arduino/smart_weather_arduino.ino), compile, and upload it.
4. The sketch sends serial at **9600 baud**, with records like:
   `WX,28.4,61.2,1008.7,39.5,0`
   This means temperature °C, humidity %, pressure hPa, approximate altitude m, and rain-wet flag (0/1).
5. The rain sensor's digital polarity may differ by board. If the wet/dry status is reversed, the code's `rainWet` logic will need to be inverted.

## Raspberry Pi dashboard

The dashboard reads **all sensor measurements from the Arduino USB serial connection**. It no longer expects a DHT11, a DS3231 RTC, or Pi GPIO rain input. The clock uses the Pi's system time.

Install dependencies and enable I2C (the dashboard itself uses USB serial for the sensors):

```bash
sudo apt update
sudo apt install -y python3-tk python3-pip
python3 -m pip install --user pyserial
```

Run the dashboard from the repository directory:

```bash
python3 weather_station.py
```

Use **LIVE MODE** only after the sensors and Arduino have been checked and are sending valid serial data. **TEST MODE** displays simulated values and does not need connected sensors. Press F11 for full screen or Esc to leave full screen.

If LIVE mode reports no Arduino, check that the UNO is connected by a USB data cable and close Arduino IDE Serial Monitor before running the dashboard. To inspect the serial stream, use Arduino IDE Serial Monitor at 9600 baud, then close it before opening the Pi dashboard (only one program can normally use the serial port at a time).

## Troubleshooting

- **BMP180 not detected:** check the module's labels and supported voltage, SDA→A4, SCL→A5, GND, and the Adafruit BMP085 library. A breakout may need a different wiring/voltage arrangement.
- **Arduino not connected:** check `ls /dev/ttyACM*` and `ls /dev/ttyUSB*` on the Pi; install `python3-serial` if needed, and ensure the current user has serial-port permission.
- **DHT22 error:** confirm the data pin is D2 in the sketch and the module pin labels are correct.
- **Rain state reversed:** invert the `digitalRead(RAIN_DO_PIN) == LOW` logic if your board has opposite polarity.
- **Any module heats up:** unplug power immediately and do not power it again until the board, voltage and polarity have been checked.

## Project files

- `weather_station.py` — Tkinter dashboard with TEST/LIVE modes and graphs
- `arduino/smart_weather_arduino.ino` — UNO firmware for BMP180, DHT22 and LM393 rain module
- `sensors/bmp180.py` — legacy Raspberry Pi I2C BMP180 driver (not used by the new serial dashboard)
- `install.sh` — legacy Pi setup script
