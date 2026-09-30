#!/usr/bin/env python3
import os
import time
from bme280_sensor import read_bme280

REFRESH_SECONDS = 5

def main():
    while True:
        os.system("clear")
        print("=" * 54)
        print("          SMART WEATHER SYSTEM")
        print("       Raspberry Pi Connect Dashboard")
        print("=" * 54)
        try:
            d = read_bme280()
            print(f"\n  Temperature : {d['temperature']:>8.2f} °C")
            print(f"  Humidity    : {d['humidity']:>8.2f} %")
            print(f"  Pressure    : {d['pressure']:>8.2f} hPa")
            print(f"  Altitude    : {d['altitude']:>8.2f} m")
            print(f"\n  Updated     : {d['timestamp']}")
            print("  Status      : SENSOR ONLINE")
        except Exception as e:
            print("\n  Status      : SENSOR ERROR")
            print(f"  Error       : {e}")
            print("\n  Check I2C and the BME280 wiring.")
        print(f"\n  Refreshing every {REFRESH_SECONDS} seconds.")
        print("  Press Ctrl+C to exit.")
        try:
            time.sleep(REFRESH_SECONDS)
        except KeyboardInterrupt:
            print("\nExiting weather dashboard.")
            return

if __name__ == "__main__":
    main()
