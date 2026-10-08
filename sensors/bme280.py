"""Lightweight BME280 temperature/pressure/humidity driver using smbus2."""
import math
import smbus2

class BME280:
    def __init__(self, bus_id=1, address=None):
        self.bus = smbus2.SMBus(bus_id)
        if address is None:
            address = self._find_address()
        self.address = address
        chip_id = self.bus.read_byte_data(self.address, 0xD0)
        if chip_id != 0x60:
            self.close()
            raise RuntimeError(f"BME280 not found at 0x{self.address:02X} (chip ID 0x{chip_id:02X})")
        self._load_calibration()
        self._configure()

    def _find_address(self):
        for address in (0x76, 0x77):
            try:
                if self.bus.read_byte_data(address, 0xD0) == 0x60:
                    return address
            except Exception:
                pass
        raise RuntimeError("BME280 not found at 0x76 or 0x77")

    def _u16(self, reg):
        d = self.bus.read_i2c_block_data(self.address, reg, 2)
        return d[0] | (d[1] << 8)

    def _s16(self, reg):
        v = self._u16(reg)
        return v - 65536 if v & 0x8000 else v

    def _load_calibration(self):
        self.dig_T1 = self._u16(0x88)
        self.dig_T2 = self._s16(0x8A)
        self.dig_T3 = self._s16(0x8C)
        self.dig_P1 = self._u16(0x8E)
        self.dig_P2 = self._s16(0x90)
        self.dig_P3 = self._s16(0x92)
        self.dig_P4 = self._s16(0x94)
        self.dig_P5 = self._s16(0x96)
        self.dig_P6 = self._s16(0x98)
        self.dig_P7 = self._s16(0x9A)
        self.dig_P8 = self._s16(0x9C)
        self.dig_P9 = self._s16(0x9E)
        self.dig_H1 = self.bus.read_byte_data(self.address, 0xA1)
        h = self.bus.read_i2c_block_data(self.address, 0xE1, 7)
        self.dig_H2 = h[0] | (h[1] << 8)
        if self.dig_H2 & 0x8000: self.dig_H2 -= 65536
        self.dig_H3 = h[2]
        self.dig_H4 = (h[3] << 4) | (h[4] & 0x0F)
        if self.dig_H4 & 0x800: self.dig_H4 -= 4096
        self.dig_H5 = (h[5] << 4) | (h[4] >> 4)
        if self.dig_H5 & 0x800: self.dig_H5 -= 4096
        self.dig_H6 = h[6] - 256 if h[6] & 0x80 else h[6]

    def _configure(self):
        self.bus.write_byte_data(self.address, 0xF2, 0x01)  # humidity x1
        self.bus.write_byte_data(self.address, 0xF5, 0x00)  # filter off
        self.bus.write_byte_data(self.address, 0xF4, 0x27)  # temp x1, pressure x1, normal mode

    def read(self):
        d = self.bus.read_i2c_block_data(self.address, 0xF7, 8)
        adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
        adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)
        adc_h = (d[6] << 8) | d[7]

        var1 = (adc_t / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
        var2 = ((adc_t / 131072.0 - self.dig_T1 / 8192.0) ** 2) * self.dig_T3
        t_fine = var1 + var2
        temperature = t_fine / 5120.0

        var1 = t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 += var1 * self.dig_P5 * 2.0
        var2 = var2 / 4.0 + self.dig_P4 * 65536.0
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        if var1 == 0:
            raise RuntimeError("BME280 pressure compensation failed")
        pressure = 1048576.0 - adc_p
        pressure = (pressure - var2 / 4096.0) * 6250.0 / var1
        var1 = self.dig_P9 * pressure * pressure / 2147483648.0
        var2 = pressure * self.dig_P8 / 32768.0
        pressure += (var1 + var2 + self.dig_P7) / 16.0

        humidity = t_fine - 76800.0
        humidity = (adc_h - (self.dig_H4 * 64.0 + self.dig_H5 / 16384.0 * humidity)) * (
            self.dig_H2 / 65536.0 * (1.0 + self.dig_H6 / 67108864.0 * humidity *
            (1.0 + self.dig_H3 / 67108864.0 * humidity)))
        humidity *= 1.0 - self.dig_H1 * humidity / 524288.0
        humidity = max(0.0, min(100.0, humidity))

        pressure_hpa = pressure / 100.0
        altitude = 44330.0 * (1.0 - math.pow(max(pressure_hpa, 1.0) / 1013.25, 0.190294957))
        return {
            "temperature": round(temperature, 1),
            "pressure": round(pressure_hpa, 1),
            "humidity": round(humidity, 1),
            "altitude": round(altitude, 1),
        }

    def close(self):
        try:
            self.bus.close()
        except Exception:
            pass
