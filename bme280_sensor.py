import time
import smbus2
import bme280

I2C_BUS = 1
BME280_ADDRESS = 0x76

bus = smbus2.SMBus(I2C_BUS)
calibration_params = bme280.load_calibration_params(bus, BME280_ADDRESS)

def read_bme280():
    data = bme280.sample(bus, BME280_ADDRESS, calibration_params)
    pressure = round(data.pressure, 2)
    return {
        "temperature": round(data.temperature, 2),
        "humidity": round(data.humidity, 2),
        "pressure": pressure,
        "altitude": round(bme280.bme280.get_altitude(pressure), 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
