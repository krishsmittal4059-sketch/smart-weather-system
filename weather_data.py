import math
import os
import time

MODE_FILE = "/opt/smart-weather-system/mode.conf"
SEA_LEVEL_HPA = 1013.25

def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def current_mode():
    try:
        with open(MODE_FILE, "r", encoding="utf-8") as f:
            mode = f.read().strip().lower()
        return mode if mode in ("test", "live") else "test"
    except OSError:
        return "test"

def set_mode(mode):
    if mode not in ("test", "live"):
        raise ValueError("Invalid mode")
    os.makedirs(os.path.dirname(MODE_FILE), exist_ok=True)
    tmp = MODE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(mode + "\n")
    os.replace(tmp, MODE_FILE)

def test_reading():
    t = time.time() / 60.0
    temperature = 27.0 + 1.8 * math.sin(t / 2.0)
    humidity = 60.0 + 5.0 * math.sin(t / 3.0 + 1.0)
    pressure = 1008.0 + 2.0 * math.sin(t / 4.0)
    altitude = 44330.0 * (1.0 - (pressure / SEA_LEVEL_HPA) ** 0.1903)
    return {
        "ok": True, "mode": "test",
        "temperature": round(temperature, 2),
        "humidity": round(humidity, 2),
        "pressure": round(pressure, 2),
        "altitude": round(altitude, 2),
        "address": None,
        "timestamp": _now()
    }

def _find_address():
    from smbus2 import SMBus
    for address in (0x76, 0x77):
        try:
            with SMBus(1) as bus:
                chip_id = bus.read_byte_data(address, 0xD0)
            if chip_id == 0x60:
                return address
        except Exception:
            pass
    return None

def live_reading():
    from bme280pi import Sensor

    address = _find_address()
    if address is None:
        raise RuntimeError("BME280 not detected at 0x76 or 0x77")

    sensor = Sensor(address=address)
    data = sensor.get_data()

    temperature = float(data["temperature"])
    humidity = float(data["humidity"])
    pressure = float(data["pressure"])
    altitude = 44330.0 * (1.0 - (pressure / SEA_LEVEL_HPA) ** 0.1903)

    return {
        "ok": True, "mode": "live",
        "temperature": round(temperature, 2),
        "humidity": round(humidity, 2),
        "pressure": round(pressure, 2),
        "altitude": round(altitude, 2),
        "address": hex(address),
        "timestamp": _now()
    }

def get_weather():
    if current_mode() == "test":
        return test_reading()
    try:
        return live_reading()
    except Exception as exc:
        return {
            "ok": False, "mode": "live", "error": str(exc),
            "temperature": None, "humidity": None,
            "pressure": None, "altitude": None,
            "address": None, "timestamp": _now()
        }
