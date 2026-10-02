import random


class BME280Sensor:
    """BME280 reader with a lightweight simulation mode for testing."""

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
        }

        if not self.test_mode:
            self._connect()

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
                    print("BME280 found at:", hex(address))
                    return
                except Exception:
                    if bus is not None:
                        try:
                            bus.close()
                        except Exception:
                            pass

            print("BME280 not found at 0x76 or 0x77")
            self.bus = None
            self.address = None
            self.calibration = None
        except Exception as error:
            print("BME280 library error:", error)
            self.bus = None
            self.address = None
            self.calibration = None

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
            }

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
        }

    def _read_test(self):
        old = self.last
        temperature = max(18.0, min(42.0, old["temperature"] + random.uniform(-0.25, 0.25)))
        humidity = max(20.0, min(90.0, old["humidity"] + random.uniform(-0.8, 0.8)))
        pressure = max(980.0, min(1030.0, old["pressure"] + random.uniform(-0.7, 0.7)))
        altitude = 44330.0 * (1.0 - (pressure / 1013.25) ** 0.1903)

        self.last = {
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "pressure": round(pressure, 1),
            "altitude": round(altitude, 1),
            "sensor_ok": True,
            "mode": "TEST",
        }
        return dict(self.last)

    def read(self):
        if self.test_mode:
            return self._read_test()

        try:
            result = self._read_real()
            self.last = dict(result)
            return result
        except Exception as error:
            print("BME280 read error:", error)
            self.bus = None
            return {
                "temperature": None,
                "humidity": None,
                "pressure": None,
                "altitude": None,
                "sensor_ok": False,
                "mode": "BME280",
            }
