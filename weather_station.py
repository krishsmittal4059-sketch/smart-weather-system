#!/usr/bin/env python3
"""RPi Weather Observatory - lightweight Raspberry Pi Tkinter dashboard."""

import math
import sys
import tkinter as tk
from collections import deque
from datetime import datetime

from bme280_sensor import BME280Sensor

UPDATE_MS = 2000
MAX_POINTS = 90
FONT = "Helvetica"

APP_BG = "#071922"
HEADER_BG = "#0e2430"
PANEL = "#122b39"
PANEL_2 = "#1a3647"
BORDER = "#2d4d5d"
GRID = "#213f4c"
TEXT = "#edf7fb"
MUTED = "#9ab5c0"
CYAN = "#5ad7ff"
GREEN = "#69e69a"
YELLOW = "#ffd166"
RED = "#ff6b6b"
PURPLE = "#9d8cff"


def clamp(value, low, high):
    return max(low, min(high, value))


class HistoryGraph(tk.Canvas):
    """Simple line graph drawn directly on a Tkinter Canvas."""

    def __init__(self, parent, title, unit, color):
        super().__init__(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        self.title = title
        self.unit = unit
        self.color = color
        self.values = []
        self.bind("<Configure>", self.redraw)

    def set_data(self, values):
        self.values = list(values)
        self.redraw()

    def redraw(self, event=None):
        if self.winfo_width() < 20 or self.winfo_height() < 20:
            return
        width = self.winfo_width()
        height = self.winfo_height()
        left, right, top, bottom = 18, 12, 18, 16
        chart_width = width - left - right
        chart_height = height - top - bottom
        self.delete("all")

        for ratio in (0.25, 0.5, 0.75):
            y = top + chart_height * ratio
            self.create_line(left, y, width - right, y, fill=GRID, width=1)

        title = self.create_text(12, 10, anchor="nw", text=self.title, fill=TEXT, font=(FONT, 11, "bold"))
        _ = title

        if not self.values:
            self.create_text(width / 2, height / 2, text="Waiting for readings ...", fill=MUTED,
                             font=(FONT, 10, "normal"))
            return

        values = self.values
        minimum = min(values)
        maximum = max(values)
        if minimum == maximum:
            minimum -= 1.0
            maximum += 1.0

        pad = (maximum - minimum) * 0.1 or 1.0
        minimum -= pad
        maximum += pad

        points = []
        for idx, value in enumerate(values):
            x = left + (idx / max(1, len(values) - 1)) * chart_width
            y = top + chart_height - ((value - minimum) / (maximum - minimum or 1.0)) * chart_height
            points.extend([x, y])

        if len(points) >= 4:
            self.create_line(*points, fill=self.color, width=2, smooth=True)
            last_x, last_y = points[-2], points[-1]
            self.create_oval(last_x - 3, last_y - 3, last_x + 3, last_y + 3, fill=self.color, outline=self.color)

        self.create_text(width - 8, 10, anchor="ne", text=f"{maximum:.1f}{self.unit}", fill=MUTED,
                         font=(FONT, 9, "normal"))


class WeatherApp:
    def __init__(self, root, fullscreen=True):
        self.root = root
        self.fullscreen = fullscreen
        self.mode = "TEST"
        self.sensor = BME280Sensor(test_mode=True)
        self.history = {
            "temperature": deque(maxlen=MAX_POINTS),
            "humidity": deque(maxlen=MAX_POINTS),
            "pressure": deque(maxlen=MAX_POINTS),
        }
        self.temp_min = None
        self.temp_max = None
        self.latest = {}
        self.sample_job = None
        self.clock_job = None

        self.root.title("RPi Weather Observatory")
        self.root.configure(bg=APP_BG)
        self.root.minsize(980, 620)
        self.root.geometry("1280x780")
        self.root.bind("<Escape>", self._escape_handler)
        self.root.bind("<F11>", self._toggle_fullscreen)

        self.build_ui()
        self.set_mode("TEST")
        self.tick_clock()
        self.sample()

    def _escape_handler(self, event=None):
        if self.fullscreen:
            self.set_fullscreen(False)
        else:
            self.root.destroy()

    def _toggle_fullscreen(self, event=None):
        self.set_fullscreen(not self.fullscreen)

    def set_fullscreen(self, value):
        self.fullscreen = bool(value)
        self.root.attributes("-fullscreen", self.fullscreen)

    def build_ui(self):
        top = tk.Frame(self.root, bg=HEADER_BG, height=74)
        top.pack(fill="x", padx=10, pady=(10, 6))
        top.pack_propagate(False)

        left = tk.Frame(top, bg=HEADER_BG)
        left.pack(side="left", padx=18, pady=10, anchor="w")
        tk.Label(left, text="◌", fg=CYAN, bg=HEADER_BG, font=(FONT, 18, "bold")).pack(side="left")
        tk.Label(left, text="RPi Weather Observatory", fg=TEXT, bg=HEADER_BG,
                 font=(FONT, 22, "bold")).pack(side="left", padx=(10, 0))

        right = tk.Frame(top, bg=HEADER_BG)
        right.pack(side="right", padx=12, pady=8)

        self.mode_button = tk.Button(
            right, text="TEST MODE", command=self.toggle_mode,
            bg="#1b4c5f", fg=TEXT, activebackground="#246c84",
            font=(FONT, 10, "bold"), bd=0, padx=12, pady=8, cursor="hand2"
        )
        self.mode_button.pack(side="left", padx=4)

        tk.Button(right, text="FULL SCREEN", command=lambda: self.set_fullscreen(True),
                  bg=PANEL_2, fg=TEXT, activebackground="#2a5873",
                  font=(FONT, 10, "bold"), bd=0, padx=10, pady=8, cursor="hand2").pack(side="left", padx=4)
        tk.Button(right, text="WINDOWED", command=lambda: self.set_fullscreen(False),
                  bg=PANEL_2, fg=TEXT, activebackground="#2a5873",
                  font=(FONT, 10, "bold"), bd=0, padx=10, pady=8, cursor="hand2").pack(side="left", padx=4)
        tk.Button(right, text="RESET HISTORY", command=self.clear_history,
                  bg=PANEL_2, fg=TEXT, activebackground="#2a5873",
                  font=(FONT, 10, "bold"), bd=0, padx=10, pady=8, cursor="hand2").pack(side="left", padx=4)
        tk.Button(right, text="EXIT", command=self.root.destroy,
                  bg="#5a2d2d", fg=TEXT, activebackground="#7d3939",
                  font=(FONT, 10, "bold"), bd=0, padx=10, pady=8, cursor="hand2").pack(side="left", padx=4)

        status = tk.Frame(self.root, bg=APP_BG)
        status.pack(fill="x", padx=10, pady=(0, 6))
        self.status_line = tk.Label(status, text="TEST MODE • Simulation active", fg=YELLOW,
                                    bg=APP_BG, font=(FONT, 10, "bold"))
        self.status_line.pack(anchor="w")

        body = tk.Frame(self.root, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=10, pady=0)

        metrics = tk.Frame(body, bg=APP_BG)
        metrics.pack(fill="x", pady=(0, 8))

        metric_titles = [
            ("Temperature", "°C", CYAN),
            ("Humidity", "%", GREEN),
            ("Pressure", "hPa", PURPLE),
            ("Altitude", "m", YELLOW),
        ]
        self.metric_vars = {}
        for idx, (name, unit, color) in enumerate(metric_titles):
            card = tk.Frame(metrics, bg=PANEL, highlightthickness=1, highlightbackground=BORDER, padx=14, pady=14)
            card.pack(side="left", fill="x", expand=True, padx=(0 if idx == 0 else 6, 0))
            tk.Label(card, text=name, fg=MUTED, bg=PANEL, font=(FONT, 10, "bold")).pack(anchor="w")
            value = tk.Label(card, text="--", fg=color, bg=PANEL, font=(FONT, 28, "bold"))
            value.pack(anchor="w", pady=(8, 0))
            self.metric_vars[name] = value

        bottom = tk.Frame(body, bg=APP_BG)
        bottom.pack(fill="both", expand=True)

        left_panel = tk.Frame(bottom, bg=APP_BG)
        left_panel.pack(side="left", fill="both", expand=True)

        self.temp_graph = HistoryGraph(left_panel, "Temperature History", "°C", CYAN)
        self.temp_graph.pack(fill="both", expand=True, padx=(0, 6), pady=(0, 6))
        self.humidity_graph = HistoryGraph(left_panel, "Humidity History", "%", GREEN)
        self.humidity_graph.pack(fill="both", expand=True, padx=(0, 6), pady=(0, 6))
        self.pressure_graph = HistoryGraph(left_panel, "Pressure History", "hPa", PURPLE)
        self.pressure_graph.pack(fill="both", expand=True, padx=(0, 6), pady=(0, 6))

        right_panel = tk.Frame(bottom, bg=APP_BG, width=350)
        right_panel.pack(side="right", fill="y", padx=(6, 0))
        right_panel.pack_propagate(False)

        info = tk.Frame(right_panel, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        info.pack(fill="both", expand=True)

        label_style = dict(bg=PANEL, fg=MUTED, font=(FONT, 10, "bold"))
        value_style = dict(bg=PANEL, fg=TEXT, font=(FONT, 14, "bold"))
        row_pad = {"padx": 16, "pady": (8, 0)}

        tk.Label(info, text="SYSTEM STATUS", **label_style).pack(anchor="w", **row_pad)
        self.sensor_status = tk.Label(info, text="SIMULATOR READY", fg=YELLOW, **value_style)
        self.sensor_status.pack(anchor="w", padx=16, pady=(0, 10))

        tk.Label(info, text="OPERATING MODE", **label_style).pack(anchor="w", **row_pad)
        self.mode_status = tk.Label(info, text="TEST", fg=YELLOW, **value_style)
        self.mode_status.pack(anchor="w", padx=16, pady=(0, 10))

        tk.Label(info, text="RAIN STATUS", **label_style).pack(anchor="w", **row_pad)
        self.rain_status = tk.Label(info, text="--", fg=TEXT, **value_style)
        self.rain_status.pack(anchor="w", padx=16, pady=(0, 10))

        tk.Label(info, text="LAST UPDATE", **label_style).pack(anchor="w", **row_pad)
        self.last_update = tk.Label(info, text="--:--:--", fg=TEXT, **value_style)
        self.last_update.pack(anchor="w", padx=16, pady=(0, 10))

        tk.Label(info, text="TEMPERATURE RANGE", **label_style).pack(anchor="w", **row_pad)
        self.range_label = tk.Label(info, text="-- / -- °C", fg=TEXT, **value_style)
        self.range_label.pack(anchor="w", padx=16, pady=(0, 10))

        tk.Label(info, text="BME280 ADDRESS", **label_style).pack(anchor="w", **row_pad)
        self.address_label = tk.Label(info, text="auto-detect", fg=TEXT, **value_style)
        self.address_label.pack(anchor="w", padx=16, pady=(0, 12))

        bottom_info = tk.Frame(right_panel, bg=PANEL, highlightthickness=1, highlightbackground=BORDER, pady=10)
        bottom_info.pack(fill="x", pady=(8, 0))
        tk.Label(bottom_info, text="SENSOR DETAIL", bg=PANEL, fg=MUTED, font=(FONT, 10, "bold")).pack(anchor="w", padx=16)
        self.sensor_detail = tk.Label(bottom_info, text="Ready for science exhibition demo.",
                                     bg=PANEL, fg=TEXT, wraplength=300, justify="left",
                                     font=(FONT, 10, "normal"))
        self.sensor_detail.pack(anchor="w", padx=16, pady=(6, 0))

    def toggle_mode(self):
        self.set_mode("LIVE" if self.mode == "TEST" else "TEST")

    def set_mode(self, mode):
        mode = mode.upper()
        self.mode = mode
        self.sensor.test_mode = (mode == "TEST")
        if self.mode == "TEST":
            self.status_line.config(text="TEST MODE • Simulation active", fg=YELLOW)
            self.mode_button.config(text="LIVE MODE", bg="#1b4c5f", activebackground="#246c84")
            self.mode_status.config(text="TEST", fg=YELLOW)
            self.sensor_status.config(text="SIMULATOR READY", fg=YELLOW)
            self.sensor_detail.config(text="Simulation active. No hardware required.")
        else:
            self.status_line.config(text="LIVE MODE • Reading BME280 sensor", fg=GREEN)
            self.mode_button.config(text="TEST MODE", bg="#245f4d", activebackground="#2f7a62")
            self.mode_status.config(text="LIVE", fg=GREEN)
            self.sensor_status.config(text="CHECKING SENSOR", fg=GREEN)
            self.sensor_detail.config(text="Scanning I²C for BME280 at 0x76 or 0x77.")
        self.clear_history(False)

    def clear_history(self, redraw=True):
        for values in self.history.values():
            values.clear()
        self.temp_min = None
        self.temp_max = None
        self.range_label.config(text="-- / -- °C")
        self.latest = {}
        if redraw:
            self.redraw()

    def read_sensor(self):
        try:
            data = self.sensor.read()
        except Exception as exc:
            data = {
                "temperature": None,
                "humidity": None,
                "pressure": None,
                "altitude": None,
                "sensor_ok": False,
                "mode": self.mode,
                "rain": False,
                "error": str(exc),
            }

        if not isinstance(data, dict):
            return {
                "temperature": None,
                "humidity": None,
                "pressure": None,
                "altitude": None,
                "sensor_ok": False,
                "mode": self.mode,
                "rain": False,
                "error": "Invalid sensor payload",
            }

        if data.get("mode") is None:
            data["mode"] = self.mode
        if "rain" not in data:
            data["rain"] = False
        if "sensor_ok" not in data:
            data["sensor_ok"] = True
        return data

    def sample(self):
        self.sample_job = None
        data = self.read_sensor()
        self.latest = data

        try:
            if data.get("sensor_ok"):
                temp = float(data.get("temperature", 0.0))
                humidity = float(data.get("humidity", 0.0))
                pressure = float(data.get("pressure", 0.0))
                if math.isfinite(temp) and math.isfinite(humidity) and math.isfinite(pressure):
                    self.history["temperature"].append(temp)
                    self.history["humidity"].append(humidity)
                    self.history["pressure"].append(pressure)
                    if self.temp_min is None or temp < self.temp_min:
                        self.temp_min = temp
                    if self.temp_max is None or temp > self.temp_max:
                        self.temp_max = temp
                else:
                    data["sensor_ok"] = False
            else:
                data["error"] = data.get("error", "Sensor disconnected or unavailable.")
        except (TypeError, ValueError):
            data["sensor_ok"] = False
            data["error"] = "Read failed."

        self.last_update.config(text=datetime.now().strftime("%H:%M:%S"))
        if self.temp_min is not None and self.temp_max is not None:
            self.range_label.config(text=f"{self.temp_min:.1f} / {self.temp_max:.1f} °C")

        self.redraw()
        self.sample_job = self.root.after(UPDATE_MS, self.sample)

    def redraw(self):
        data = self.latest or {}
        temp = data.get("temperature")
        humidity = data.get("humidity")
        pressure = data.get("pressure")
        altitude = data.get("altitude")

        if temp is None:
            self.metric_vars["Temperature"].config(text="--")
        else:
            self.metric_vars["Temperature"].config(text=f"{float(temp):.1f}")

        if humidity is None:
            self.metric_vars["Humidity"].config(text="--")
        else:
            self.metric_vars["Humidity"].config(text=f"{float(humidity):.1f}")

        if pressure is None:
            self.metric_vars["Pressure"].config(text="----")
        else:
            self.metric_vars["Pressure"].config(text=f"{float(pressure):.1f}")

        if altitude is None:
            self.metric_vars["Altitude"].config(text="--")
        else:
            self.metric_vars["Altitude"].config(text=f"{float(altitude):.1f}")

        if self.mode == "TEST":
            self.sensor_status.config(text="SIMULATOR READY", fg=YELLOW)
            self.mode_status.config(text="TEST", fg=YELLOW)
            self.sensor_detail.config(text="Simulation active. No hardware required.")
        elif data.get("sensor_ok"):
            self.sensor_status.config(text="BME280 ONLINE", fg=GREEN)
            self.mode_status.config(text="LIVE", fg=GREEN)
            self.sensor_detail.config(text="BME280 detected and streaming live observations.")
        else:
            self.sensor_status.config(text="SENSOR OFFLINE", fg=RED)
            self.mode_status.config(text="LIVE", fg=GREEN)
            self.sensor_detail.config(text=data.get("error", "BME280 not detected. Check I²C wiring and address 0x76 / 0x77."))

        if data.get("rain"):
            self.rain_status.config(text="RAIN DETECTED", fg=YELLOW)
        else:
            self.rain_status.config(text="NO RAIN", fg=GREEN)

        if self.mode == "TEST":
            self.address_label.config(text="simulated")
        elif self.sensor.address is not None:
            self.address_label.config(text=f"0x{self.sensor.address:02x}")
        else:
            self.address_label.config(text="not found")

        self.temp_graph.set_data(self.history["temperature"])
        self.humidity_graph.set_data(self.history["humidity"])
        self.pressure_graph.set_data(self.history["pressure"])

    def tick_clock(self):
        self.clock_job = self.root.after(1000, self.tick_clock)


def main():
    root = tk.Tk()
    app = WeatherApp(root, fullscreen="--windowed" not in sys.argv)
    app.set_fullscreen(app.fullscreen)
    root.mainloop()


if __name__ == "__main__":
    main()
