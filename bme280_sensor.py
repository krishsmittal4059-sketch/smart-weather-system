#!/usr/bin/env python3
"""BME280 sensor helper with lightweight simulated TEST mode."""

import random
import threading


class BME280Sensor:
    """Read a real BME280 sensor or generate realistic test data."""

    def __init__(self, test_mode=True):
        self.test_mode = test_mode
        self.address = None
        self.bus = None
        self.calibration = None
        self.last = {
            "temperature": 27.0,
            "humidity": 60.0,
            "pressure": 1008.0,
            "altitude": 40.0,
            "sensor_ok": True,
            "mode": "TEST",
            "rain": False,
        }
        self._lock = threading.Lock()
        self._rain_bias = 0.5
        if not self.test_mode:
            self._connect()

    def _reset_bus(self):
        if self.bus is not None:
            try:
                self.bus.close()
            except Exception:
                pass
        self.bus = None
        self.address = None
        self.calibration = None

    def _connect(self):
        try:
            import smbus2
            import bme280

            self.smbus2 = smbus2
            self.bme280 = bme280

            for address in (0x76, 0x77):
                bus = None
                try:
                    bus = smbus2.SMBus(1)
                    calibration = bme280.load_calibration_params(bus, address)
                    self.bus = bus
                    self.address = address
                    self.calibration = calibration
                    print(f"[BME280] Found at I2C address 0x{address:02x}")
                    return
                except Exception:
                    if bus is not None:
                        try:
                            bus.close()
                        except Exception:
                            pass

            print("[BME280] No device found at I2C address 0x76 or 0x77")
            self._reset_bus()
        except Exception as error:
            print(f"[BME280] Import/setup error: {error}")
            self._reset_bus()

    def _read_real(self):
        if self.bus is None:
            self._connect()

        if self.bus is None:
            return {
                "temperature": None,
                "humidity": None,
                "pressure": None,
                "altitude": None,
                "sensor_ok": False,
                "mode": "BME280",
                "rain": self._read_rain_sensor(),
            }

        try:
            data = self.bme280.sample(self.bus, self.address, self.calibration)
            pressure = float(data.pressure)
            altitude = 44330.0 * (1.0 - (pressure / 1013.25) ** 0.1903)
            return {
                "temperature": round(float(data.temperature), 1),
                "humidity": round(float(data.humidity), 1),
                "pressure": round(pressure, 1),
                "altitude": round(altitude, 1),
                "sensor_ok": True,
                "mode": "BME280",
                "rain": self._read_rain_sensor(),
            }
        except Exception:
            self._reset_bus()
            return {
                "temperature": None,
                "humidity": None,
                "pressure": None,
                "altitude": None,
                "sensor_ok": False,
                "mode": "BME280",
                "rain": False,
            }

    def _read_rain_sensor(self):
        """Optional GPIO17 rain sensor support.
        Returns True when rain is detected; returns False if not available.
        """
        try:
            import RPi.GPIO as GPIO

            GPIO.setmode(GPIO.BCM)
            GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            rain_detected = GPIO.input(17) == 0
            GPIO.cleanup(17)
            return rain_detected
        except Exception:
            return False

    def _read_test(self):
        previous = self.last
        temperature = max(18.0, min(42.0, previous["temperature"] + random.uniform(-0.35, 0.35)))
        humidity = max(20.0, min(95.0, previous["humidity"] + random.uniform(-0.8, 0.8)))
        pressure = max(980.0, min(1035.0, previous["pressure"] + random.uniform(-0.8, 0.8)))
        altitude = 44330.0 * (1.0 - (pressure / 1013.25) ** 0.1903)

        self._rain_bias += random.uniform(-0.1, 0.1)
        self._rain_bias = max(0.0, min(1.0, self._rain_bias))
        rain = random.random() < 0.25 or (previous.get("rain", False) and random.random() < 0.70)

        self.last = {
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "pressure": round(pressure, 1),
            "altitude": round(altitude, 1),
            "sensor_ok": True,
            "mode": "TEST",
            "rain": rain,
        }
        return dict(self.last)

    def read(self):
        with self._lock:
            if self.test_mode:
                return self._read_test()

            try:
                result = self._read_real()
                self.last = dict(result)
                return result
            except Exception as error:
                print(f"[BME280] Read error: {error}")
                self._reset_bus()
                return {
                    "temperature": None,
                    "humidity": None,
                    "pressure": None,
                    "altitude": None,
                    "sensor_ok": False,
                    "mode": "BME280",
                    "rain": False,
                }

    def close(self):
        self._reset_bus()


if __name__ == "__main__":
    sensor = BME280Sensor(test_mode=True)
    print(sensor.read())
