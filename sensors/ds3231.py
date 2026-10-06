"""Minimal DS3231 RTC reader over I2C."""
from datetime import datetime

class DS3231:
    def __init__(self,bus_id=1,address=0x68):
        import smbus2
        self.bus=smbus2.SMBus(bus_id); self.address=address
    @staticmethod
    def _bcd(value): return (value & 0x0F)+((value>>4)*10)
    def read_datetime(self):
        d=self.bus.read_i2c_block_data(self.address,0x00,7)
        sec=self._bcd(d[0]&0x7F); minute=self._bcd(d[1]); hour=self._bcd(d[2]&0x3F)
        day=self._bcd(d[4]); month=self._bcd(d[5]&0x1F); year=2000+self._bcd(d[6])
        return datetime(year,month,day,hour,minute,sec)
    def close(self):
        try: self.bus.close()
        except Exception: pass
