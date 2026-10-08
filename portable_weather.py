#!/usr/bin/env python3
"""Pocket Weather mode for the RPi Weather Observatory.

Runs without a desktop/X display and shows live local sensor readings on the
I2C OLED. Intended for a portable Raspberry Pi 1 Model B+ setup.
"""
import time
from datetime import datetime

from sensors.bme280 import BME280
from sensors.dht11 import DHT11
from sensors.ds3231 import DS3231
from sensors.rain_sensor import RainSensor
from sensors.oled import OLEDDisplay

UPDATE_SECONDS = 2.5

def main():
    oled = OLEDDisplay()
    bme = BME280()
    dht = DHT11()
    rtc = DS3231()
    rain = RainSensor()

    while True:
        temperature = humidity = pressure = None
        clock = datetime.now()
        raining = False

        try:
            data = bme.read()
            temperature = data.get("temperature")
            pressure = data.get("pressure")
        except Exception:
            pass

        try:
            data = dht.read()
            humidity = data.get("humidity")
            if temperature is None:
                temperature = data.get("temperature")
        except Exception:
            pass

        try:
            clock = rtc.read_datetime()
        except Exception:
            pass

        try:
            raining = rain.is_raining()
        except Exception:
            pass

        oled.show(
            temperature=temperature,
            humidity=humidity,
            pressure=pressure,
            rain=raining,
            clock=clock,
            mode="LIVE",
        )
        time.sleep(UPDATE_SECONDS)

if __name__ == "__main__":
    main()
