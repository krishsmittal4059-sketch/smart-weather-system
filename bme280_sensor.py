#!/usr/bin/env python3
"""BME280 sensor reader with lightweight TEST mode simulation."""
import random
import threading


class BME280Sensor:
    """BME280 reader with a lightweight simulation mode for testing.
    
    LIVE mode: Reads real BME280 sensor via I2C (auto-detect 0x76 or 0x77)
    TEST mode: Generates realistic simulated weather data
    """

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
        self._rain_pattern = 0  # For rain simulation
        self._lock = threading.Lock()

        if not self.test_mode:
            self._connect()

    def _connect(self):
        """Attempt to connect to BME280 at I2C addresses 0x76 or 0x77."""
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
                    print(f"[BME280] Found at I²C address {hex(address)}")
                    return
                except Exception:
                    if bus is not None:
                        try:
                            bus.close()
                        except Exception:
                            pass

            print("[BME280] Not found at I²C 0x76 or 0x77")
            self.bus = None
            self.address = None
            self.calibration = None
        except Exception as error:
            print(f"[BME280] Library error: {error}")
            self.bus = None
            self.address = None
            self.calibration = None

    def _read_real(self):
        """Read actual BME280 sensor data."""
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
                "rain": False,
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
            self.bus = None
            self.address = None
            self.calibration = None
            return {
                "temperature": None,
                "humidity": None,
                "pressure": None,
                "altitude": None,
                "sensor_ok": False,
                "mode": "BME280",
                "rain": False,
            }

    def _read_test(self):
        """Generate realistic simulated weather data."""
        old = self.last
        
        # Realistic weather patterns with daily cycles
        temperature = max(18.0, min(42.0, old["temperature"] + random.uniform(-0.25, 0.25)))
        humidity = max(20.0, min(95.0, old["humidity"] + random.uniform(-0.8, 0.8)))
        pressure = max(980.0, min(1030.0, old["pressure"] + random.uniform(-0.7, 0.7)))
        altitude = 44330.0 * (1.0 - (pressure / 1013.25) ** 0.1903)
        
        # Realistic rain pattern (occasional rain events)
        self._rain_pattern += random.uniform(-0.1, 0.1)
        self._rain_pattern = max(0, min(1.0, self._rain_pattern))
        rain = self._rain_pattern > 0.7  # Rain occurs ~30% of the time on average

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

    def _read_rain_sensor(self):
        """Read rain sensor from GPIO17 (real hardware).
        
        Returns True if rain is detected (GPIO17 low/active).
        """
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(17, GPIO.IN)
            rain = not GPIO.input(17)  # Active low
            GPIO.cleanup(17)
            return rain
        except Exception:
            # GPIO not available or sensor not connected
            return False

    def read(self):
        """Read sensor data (real or simulated).
        
        Returns a dict with keys:
          - temperature: float (°C)
          - humidity: float (%)
          - pressure: float (hPa)
          - altitude: float (m)
          - sensor_ok: bool
          - mode: str ("TEST" or "BME280")
          - rain: bool
        """
        with self._lock:
            if self.test_mode:
                return self._read_test()

            try:
                result = self._read_real()
                self.last = dict(result)
                return result
            except Exception as error:
                print(f"[BME280] Read error: {error}")
                if self.bus is not None:
                    try:
                        self.bus.close()
                    except Exception:
                        pass
                self.bus = None
                self.address = None
                self.calibration = None
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
        """Cleanup resources."""
        if self.bus is not None:
            try:
                self.bus.close()
            except Exception:
                pass
