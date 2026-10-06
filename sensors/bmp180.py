"""Lightweight BMP180 driver using smbus2 only."""
import math
import time

class BMP180:
    def __init__(self, bus_id=1, address=0x77):
        import smbus2
        self.bus = smbus2.SMBus(bus_id)
        self.address = address
        self._load_calibration()

    def _read_s16(self, reg):
        value = self.bus.read_word_data(self.address, reg)
        value = ((value & 0xFF) << 8) | (value >> 8)
        return value - 65536 if value & 0x8000 else value

    def _read_u16(self, reg):
        value = self.bus.read_word_data(self.address, reg)
        return ((value & 0xFF) << 8) | (value >> 8)

    def _load_calibration(self):
        self.ac1=self._read_s16(0xAA); self.ac2=self._read_s16(0xAC)
        self.ac3=self._read_s16(0xAE); self.ac4=self._read_u16(0xB0)
        self.ac5=self._read_u16(0xB2); self.ac6=self._read_u16(0xB4)
        self.b1=self._read_s16(0xB6); self.b2=self._read_s16(0xB8)
        self.mb=self._read_s16(0xBA); self.mc=self._read_s16(0xBC); self.md=self._read_s16(0xBE)

    def _raw_temperature(self):
        self.bus.write_byte_data(self.address, 0xF4, 0x2E)
        time.sleep(0.005)
        return self.bus.read_word_data(self.address, 0xF6) >> 8 | (self.bus.read_byte_data(self.address, 0xF6) << 8)

    def _read_raw(self, command, delay, length=2):
        self.bus.write_byte_data(self.address, 0xF4, command)
        time.sleep(delay)
        data=self.bus.read_i2c_block_data(self.address, 0xF6, length)
        return (data[0] << 8) | data[1] | ((data[2] << 16) if length == 3 else 0)

    def read(self):
        ut=self._read_raw(0x2E, 0.005, 2)
        x1=((ut-self.ac6)*self.ac5)>>15
        x2=(self.mc<<11)//(x1+self.md)
        b5=x1+x2
        temperature=((b5+8)>>4)/10.0

        up=self._read_raw(0x34, 0.005, 3) >> 8
        b6=b5-4000
        x1=(self.b2*((b6*b6)>>12))>>11
        x2=(self.ac2*b6)>>11
        x3=x1+x2
        b3=((self.ac1*4+x3)+2)//4
        x1=(self.ac3*b6)>>13
        x2=(self.b1*((b6*b6)>>12))>>16
        x3=((x1+x2)+2)//4
        b4=(self.ac4*(x3+32768))>>15
        b7=(up-b3)*50000
        pressure=(b7*2)//b4 if b7 < 0x80000000 else (b7//b4)*2
        x1=(pressure>>8)*(pressure>>8)
        x1=(x1*3038)>>16
        x2=(-7357*pressure)>>16
        pressure += (x1+x2+3791)>>4
        pressure=float(pressure)
        altitude=44330.0*(1.0-math.pow(pressure/101325.0,0.190294957))
        return {"temperature":round(temperature,1),"pressure":round(pressure/100.0,1),"altitude":round(altitude,1)}

    def close(self):
        try: self.bus.close()
        except Exception: pass
