# Smart Weather Observatory

A lightweight weather-station project for Raspberry Pi 1 Model B+ using the original dark Tkinter dashboard. The Arduino UNO reads a DHT22 and a rain sensor, then sends readings to the Pi over USB serial. **This version does not use a BMP180.**

## Hardware

- Raspberry Pi 1 Model B+ running Raspberry Pi OS Trixie
- Arduino UNO and USB data cable
- DHT22 temperature/humidity module
- LM393 rain sensor module and rain plate
- Breadboard and jumper wires

## Safety before wiring

If a sensor module or board becomes hot immediately after power-on, unplug it and do not power it again until the supply voltage, pin labels, polarity, and wiring have been checked. A hot module can indicate reversed power, a short, incompatible voltage, or damage. Ask a knowledgeable adult/teacher to inspect uncertain wiring.

## Wiring

### DHT22 module → Arduino UNO

Use the printed VCC/+, DATA/OUT, and GND/- labels on your exact module because pin order can vary.

| DHT22 module | Arduino UNO |
|---|---|
| VCC/+ | Supported supply voltage for the module |
| DATA/OUT | D2 |
| GND/- | GND |

### LM393 rain module → Arduino UNO

| Rain module | Arduino UNO |
|---|---|
| VCC | Voltage specified on the exact module |
| GND | GND |
| DO | D3 |
| AO | A0 |

Connect the separate rain plate to its matching connector on the comparator module. Rain sensor polarity and analog values vary by module, so test and calibrate the wet/dry readings.

### Arduino UNO → Raspberry Pi

Connect the UNO to the Pi using a USB **data** cable. Do not connect the Arduino's 5V pin or 5V signals directly to Raspberry Pi GPIO pins.

## Arduino setup

1. Open Arduino IDE and select **Arduino UNO**.
2. In Library Manager install:
   - **DHT sensor library by Adafruit**
   - **Adafruit Unified Sensor**, if requested
3. Open [arduino/smart_weather_arduino.ino](arduino/smart_weather_arduino.ino), verify, and upload.
4. Set the Serial Monitor baud rate to **9600** when testing the sketch. Close Serial Monitor before running the dashboard.
5. The sketch reports temperature, humidity, rain analog value, estimated plate wetness, digital rain threshold, and plate status. The wetness percentage is only an estimate; adjust DRY_VALUE and WET_VALUE in the sketch after measuring your dry and wet plate values.

## Raspberry Pi setup

From the repository directory, install the system packages:

    sudo apt update
    sudo apt install -y python3-tk python3-serial

Run the original dashboard:

    python3 weather_station.py

The dashboard opens in full screen by default. Press **F11** to toggle full screen, **Esc** to leave full screen, or use the on-screen controls. **TEST MODE** shows simulated readings. Click **LIVE MODE** to read the Arduino over USB.

The dashboard keeps the existing dark design, temperature range, and history graphs, and displays DHT22 temperature/humidity plus rain analog value, plate wetness, and rain status. No pressure/altitude readings are shown because the BMP180 has been removed.

## Troubleshooting

- **Arduino not found:** run ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null. Make sure the Arduino is connected with a USB data cable.
- **No live readings:** close Arduino IDE Serial Monitor; only one program can normally use the serial port at a time.
- **Serial permission error:** run sudo usermod -aG dialout "$USER" and then log out and log back in.
- **DHT22 read error:** confirm the module labels and that DATA/OUT is connected to D2.
- **Rain status seems reversed or wetness percentage is inaccurate:** calibrate the rain module and the DRY_VALUE/WET_VALUE values in the sketch.
- **A module heats up:** disconnect power immediately and have the module and wiring checked before reconnecting it.

## Project files

- weather_station.py — original Tkinter dashboard, adapted for Arduino DHT22 and rain data
- arduino/smart_weather_arduino.ino — Arduino UNO firmware without BMP180
- sensors/ — legacy sensor helper modules; not required for the Arduino USB dashboard
