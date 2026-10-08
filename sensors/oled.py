#!/usr/bin/env python3
"""Optional I2C OLED status display for the RPi Weather Observatory."""
import os

class OLEDDisplay:
    def __init__(self):
        self.enabled = os.getenv("OLED_ENABLED", "1").lower() not in ("0", "false", "no")
        self.driver = os.getenv("OLED_DRIVER", "sh1106").lower()
        self.address = int(os.getenv("OLED_ADDR", "0x3c"), 0)
        self.width = int(os.getenv("OLED_WIDTH", "128"))
        self.height = int(os.getenv("OLED_HEIGHT", "64"))
        self.device = None
        self.available = False
        self.error = ""
        if not self.enabled:
            self.error = "disabled"
            return
        try:
            from luma.core.interface.serial import i2c
            from luma.core.render import canvas
            serial = i2c(port=1, address=self.address)
            if self.driver == "ssd1306":
                from luma.oled.device import ssd1306
                self.device = ssd1306(serial, width=self.width, height=self.height)
            elif self.driver == "sh1106":
                from luma.oled.device import sh1106
                self.device = sh1106(serial, width=self.width, height=self.height)
            else:
                raise ValueError("OLED_DRIVER must be sh1106 or ssd1306")
            self._canvas = canvas
            self.available = True
        except Exception as exc:
            self.error = str(exc)
    def show(self, temperature=None, humidity=None, pressure=None, rain=False, clock=None, mode="TEST"):
        if not self.available:
            return
        def value(v, suffix=""):
            return "--" if v is None else f"{v}{suffix}"
        try:
            with self._canvas(self.device) as draw:
                draw.rectangle((0, 0, self.width - 1, self.height - 1), outline=255)
                draw.text((4, 2), "RPi WEATHER", fill=255)
                draw.text((4, 14), f"T:{value(temperature, 'C')}  H:{value(humidity, '%')}", fill=255)
                draw.text((4, 26), f"P:{value(pressure, 'hPa')}", fill=255)
                draw.text((4, 38), "RAIN: YES" if rain else "RAIN: NO", fill=255)
                if clock is not None and hasattr(clock, "strftime"):
                    draw.text((4, 50), clock.strftime("%H:%M:%S"), fill=255)
                draw.text((82, 50), mode, fill=255)
        except Exception as exc:
            self.error = str(exc)
            self.available = False
