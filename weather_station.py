#!/usr/bin/env python3
"""RPi Weather Observatory: lightweight Arduino USB dashboard for Raspberry Pi 1 B+."""
import random
import sys
import tkinter as tk
from collections import deque
from datetime import datetime

UPDATE_MS = 1000
MAX_POINTS = 90
BG = "#071922"
HEADER = "#0e2430"
PANEL = "#122b39"
PANEL2 = "#1a3647"
BORDER = "#2d4d5d"
GRID = "#213f4c"
TEXT = "#edf7fb"
MUTED = "#9ab5c0"
CYAN = "#5ad7ff"
GREEN = "#69e69a"
YELLOW = "#ffd166"
RED = "#ff6b6b"
PURPLE = "#9d8cff"


class HistoryGraph(tk.Canvas):
    def __init__(self, parent, title, unit, accent):
        super().__init__(parent, bg=PANEL, highlightthickness=1,
                         highlightbackground=BORDER)
        self.title, self.unit, self.accent = title, unit, accent
        self.values = []
        self.bind("<Configure>", self.redraw)

    def set_data(self, values):
        self.values = list(values)
        self.redraw()

    def redraw(self, event=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 30 or h < 30:
            return
        self.delete("all")
        left, right, top, bottom = 24, 12, 28, 18
        cw, ch = w - left - right, h - top - bottom
        self.create_text(12, 8, anchor="nw", text=self.title, fill=TEXT,
                         font=("Helvetica", 11, "bold"))
        for q in (.25, .5, .75):
            y = top + ch * q
            self.create_line(left, y, w - right, y, fill=GRID)
        if not self.values:
            self.create_text(w / 2, h / 2, text="Waiting for readings...",
                             fill=MUTED, font=("Helvetica", 10))
            return
        lo, hi = min(self.values), max(self.values)
        if lo == hi:
            lo -= 1
            hi += 1
        pad = max((hi - lo) * .1, .01)
        lo -= pad
        hi += pad
        pts = []
        for i, value in enumerate(self.values):
            x = left + (i / max(1, len(self.values) - 1)) * cw
            y = top + ch - (value - lo) / (hi - lo) * ch
            pts.extend([x, y])
        if len(pts) >= 4:
            self.create_line(*pts, fill=self.accent, width=2, smooth=True)
            x, y = pts[-2:]
            self.create_oval(x - 3, y - 3, x + 3, y + 3,
                             fill=self.accent, outline=self.accent)
        self.create_text(w - 8, 9, anchor="ne",
                         text=f"{max(self.values):.1f}{self.unit}",
                         fill=MUTED, font=("Helvetica", 9))


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.mode = "TEST"
        self.fullscreen = "--windowed" not in sys.argv
        self.history = {
            key: deque(maxlen=MAX_POINTS)
            for key in ("temperature", "humidity", "wetness")
        }
        self.temp_min = None
        self.temp_max = None
        self.latest = {}
        self.sim = {"temperature": 26.0, "humidity": 60.0, "wetness": 8.0}
        self.serial = None
        self.serial_port = "Arduino not connected"
        self.last_packet_time = None
        self.pending = {}
        root.title("RPi Weather Observatory")
        root.configure(bg=BG)
        root.minsize(900, 600)
        root.geometry("1280x780")
        root.bind("<F11>", lambda e: self.set_fullscreen(not self.fullscreen))
        root.bind("<Escape>", lambda e: self.set_fullscreen(False))
        self.build_ui()
        self.set_fullscreen(self.fullscreen)
        self.sample()

    def build_ui(self):
        top = tk.Frame(self.root, bg=HEADER, height=76)
        top.pack(fill="x", padx=10, pady=(10, 6))
        top.pack_propagate(False)
        tk.Label(top, text="◌  RPi Weather Observatory", bg=HEADER, fg=TEXT,
                 font=("Helvetica", 22, "bold")).pack(side="left", padx=18, pady=18)
        controls = tk.Frame(top, bg=HEADER)
        controls.pack(side="right", padx=12)
        self.mode_btn = tk.Button(
            controls, text="LIVE MODE", command=self.toggle_mode,
            bg="#1b4c5f", fg=TEXT, bd=0, padx=12, pady=8,
            font=("Helvetica", 10, "bold"))
        self.mode_btn.pack(side="left", padx=3)
        for text, command in (
            ("FULL SCREEN", lambda: self.set_fullscreen(True)),
            ("WINDOWED", lambda: self.set_fullscreen(False)),
            ("RESET HISTORY", self.clear_history),
            ("EXIT", self.close),
        ):
            tk.Button(
                controls, text=text, command=command,
                bg=PANEL2 if text != "EXIT" else "#5a2d2d",
                fg=TEXT, bd=0, padx=10, pady=8,
                font=("Helvetica", 10, "bold")).pack(side="left", padx=3)

        self.status = tk.Label(
            self.root, text="TEST MODE • Simulation active", bg=BG, fg=YELLOW,
            font=("Helvetica", 10, "bold"))
        self.status.pack(anchor="w", padx=12, pady=(0, 6))

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=10)
        cards = tk.Frame(body, bg=BG)
        cards.pack(fill="x", pady=(0, 8))
        self.metric = {}
        metrics = (
            ("Temperature", "°C", CYAN),
            ("Humidity", "%", GREEN),
            ("Rain Wetness", "%", PURPLE),
        )
        for i, (name, unit, accent) in enumerate(metrics):
            card = tk.Frame(cards, bg=PANEL, highlightthickness=1,
                            highlightbackground=BORDER, padx=14, pady=12)
            card.pack(side="left", fill="x", expand=True,
                      padx=(0 if i == 0 else 6, 0))
            tk.Label(card, text=name, bg=PANEL, fg=MUTED,
                     font=("Helvetica", 10, "bold")).pack(anchor="w")
            value = tk.Label(card, text="--", bg=PANEL, fg=accent,
                             font=("Helvetica", 28, "bold"))
            value.pack(anchor="w", pady=(5, 0))
            self.metric[name] = value

        lower = tk.Frame(body, bg=BG)
        lower.pack(fill="both", expand=True)
        charts = tk.Frame(lower, bg=BG)
        charts.pack(side="left", fill="both", expand=True)
        self.g_temp = HistoryGraph(charts, "TEMPERATURE HISTORY", " °C", CYAN)
        self.g_temp.pack(fill="both", expand=True, padx=(0, 6), pady=(0, 6))
        self.g_hum = HistoryGraph(charts, "HUMIDITY HISTORY", " %", GREEN)
        self.g_hum.pack(fill="both", expand=True, padx=(0, 6), pady=(0, 6))
        self.g_wet = HistoryGraph(charts, "RAIN PLATE WETNESS HISTORY", " %", PURPLE)
        self.g_wet.pack(fill="both", expand=True, padx=(0, 6))

        side = tk.Frame(lower, bg=BG, width=340)
        side.pack(side="right", fill="y")
        side.pack_propagate(False)
        info = tk.Frame(side, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER)
        info.pack(fill="both", expand=True)
        self.fields = {}
        for key, label in (
            ("system", "SYSTEM STATUS"),
            ("mode", "OPERATING MODE"),
            ("rain", "RAIN SENSOR"),
            ("analog", "RAIN ANALOG VALUE"),
            ("clock", "PI SYSTEM TIME"),
            ("range", "TEMPERATURE RANGE"),
            ("sensors", "ARDUINO / SENSORS"),
        ):
            tk.Label(info, text=label, bg=PANEL, fg=MUTED,
                     font=("Helvetica", 10, "bold")).pack(
                         anchor="w", padx=16, pady=(8, 1))
            value = tk.Label(info, text="--", bg=PANEL, fg=TEXT,
                             font=("Helvetica", 12, "bold"),
                             wraplength=300, justify="left")
            value.pack(anchor="w", padx=16, pady=(0, 3))
            self.fields[key] = value
        self.detail = tk.Label(
            side, text="TEST mode works without hardware.", bg=PANEL2,
            fg=TEXT, wraplength=300, justify="left", font=("Helvetica", 10),
            padx=12, pady=10)
        self.detail.pack(fill="x", pady=(8, 0))

    def set_fullscreen(self, value):
        self.fullscreen = bool(value)
        self.root.attributes("-fullscreen", self.fullscreen)

    def toggle_mode(self):
        self.set_mode("LIVE" if self.mode == "TEST" else "TEST")

    def set_mode(self, mode):
        self.mode = mode
        self.mode_btn.config(text="TEST MODE" if mode == "LIVE" else "LIVE MODE")
        self.status.config(
            text=("LIVE MODE • DHT22 + rain sensor via Arduino USB"
                  if mode == "LIVE" else "TEST MODE • Simulation active"),
            fg=GREEN if mode == "LIVE" else YELLOW)
        if mode == "TEST":
            self.close_serial()
        self.clear_history()

    def clear_history(self):
        for values in self.history.values():
            values.clear()
        self.temp_min = self.temp_max = None
        self.redraw()

    def close_serial(self):
        try:
            if self.serial is not None and self.serial.is_open:
                self.serial.close()
        except Exception:
            pass
        self.serial = None

    def connect_serial(self):
        import serial
        from serial.tools import list_ports
        ports = [p.device for p in list_ports.comports()]
        preferred = [p for p in ports if "ttyACM" in p or "ttyUSB" in p]
        for port in preferred + [p for p in ports if p not in preferred]:
            try:
                self.serial = serial.Serial(port, 9600, timeout=0.03)
                self.serial_port = port
                self.serial.reset_input_buffer()
                return
            except Exception:
                self.serial = None
        raise RuntimeError("Arduino USB serial port not found")

    def read_live(self):
        if self.serial is None or not self.serial.is_open:
            self.connect_serial()
        # Read only data currently waiting; never block the dashboard for long.
        for _ in range(100):
            if self.serial.in_waiting <= 0:
                break
            line = self.serial.readline().decode("utf-8", "ignore").strip()
            if not line:
                continue
            print(line, flush=True)
            if line.startswith("Temperature:"):
                try:
                    self.pending["temperature"] = float(
                        line.split(":", 1)[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
            elif line.startswith("Humidity:"):
                try:
                    self.pending["humidity"] = float(
                        line.split(":", 1)[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
            elif line.startswith("Rain analog value:"):
                try:
                    self.pending["rain_analog"] = int(
                        line.split(":", 1)[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
            elif line.startswith("Estimated plate wetness:"):
                try:
                    self.pending["wetness"] = float(
                        line.split(":", 1)[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
            elif line.startswith("Rain threshold output:"):
                self.pending["rain_trigger"] = line.split(":", 1)[1].strip()
            elif line.startswith("Plate status:"):
                self.pending["rain_status"] = line.split(":", 1)[1].strip()
            elif line == "DHT22 read error!":
                self.pending["dht_error"] = True
            elif line.startswith("===== WEATHER REPORT"):
                self.pending["dht_error"] = False

        if "temperature" not in self.pending or "humidity" not in self.pending:
            raise RuntimeError("Waiting for Arduino weather readings")
        data = dict(self.pending)
        data.update({
            "mode": "LIVE",
            "sensor_ok": not data.get("dht_error", False),
            "rtc": datetime.now(),
            "arduino_status": self.serial_port,
            "errors": [],
        })
        self.last_packet_time = datetime.now()
        return data

    def read_test(self):
        self.sim["temperature"] = max(
            18, min(40, self.sim["temperature"] + random.uniform(-.25, .25)))
        self.sim["humidity"] = max(
            25, min(90, self.sim["humidity"] + random.uniform(-.8, .8)))
        self.sim["wetness"] = max(
            0, min(100, self.sim["wetness"] + random.uniform(-2.0, 2.0)))
        return {
            "temperature": round(self.sim["temperature"], 1),
            "humidity": round(self.sim["humidity"], 1),
            "wetness": round(self.sim["wetness"], 1),
            "rain_analog": int(900 - self.sim["wetness"] * 6),
            "rain_trigger": "NOT TRIGGERED",
            "rain_status": "DRY / LIGHTLY WET" if self.sim["wetness"] < 30 else "DAMP",
            "sensor_ok": True,
            "mode": "TEST",
            "rtc": datetime.now(),
            "errors": [],
        }

    def sample(self):
        try:
            data = self.read_test() if self.mode == "TEST" else self.read_live()
            self.latest = data
            for key in ("temperature", "humidity", "wetness"):
                value = data.get(key)
                if value is not None:
                    self.history[key].append(float(value))
            temperature = data.get("temperature")
            if temperature is not None:
                self.temp_min = temperature if self.temp_min is None else min(
                    self.temp_min, temperature)
                self.temp_max = temperature if self.temp_max is None else max(
                    self.temp_max, temperature)
        except Exception as error:
            self.latest.setdefault("errors", [])
            self.latest["errors"] = [str(error)]
            self.latest["sensor_ok"] = False
            self.latest["arduino_status"] = self.serial_port
        self.redraw()
        self.root.after(UPDATE_MS, self.sample)

    def redraw(self):
        data = self.latest
        for label, key, unit in (
            ("Temperature", "temperature", " °C"),
            ("Humidity", "humidity", " %"),
            ("Rain Wetness", "wetness", " %"),
        ):
            value = data.get(key)
            self.metric[label].config(
                text=f"{float(value):.1f}{unit}" if value is not None else "--")
        self.fields["clock"].config(text=datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
        self.fields["mode"].config(text=self.mode,
                                   fg=GREEN if self.mode == "LIVE" else YELLOW)
        rain_status = data.get("rain_status", "Waiting for readings")
        self.fields["rain"].config(
            text=rain_status,
            fg=YELLOW if data.get("wetness", 0) >= 30 else GREEN)
        analog = data.get("rain_analog")
        self.fields["analog"].config(text=str(analog) if analog is not None else "--")
        self.fields["range"].config(
            text=f"{self.temp_min:.1f} °C  /  {self.temp_max:.1f} °C"
            if self.temp_min is not None else "--")
        if self.mode == "TEST":
            self.fields["system"].config(text="SIMULATION READY", fg=YELLOW)
            self.fields["sensors"].config(text="TEST DATA")
            self.detail.config(
                text="Simulation active. Switch to LIVE MODE when the Arduino is connected.")
        else:
            errors = data.get("errors", [])
            ok = data.get("sensor_ok", False) and not errors
            self.fields["system"].config(
                text="LIVE • OK" if ok else "LIVE • WAITING / ERROR",
                fg=GREEN if ok else RED)
            self.fields["sensors"].config(
                text=data.get("arduino_status", "Arduino unavailable"))
            self.detail.config(text="; ".join(errors) if errors else
                               "Live DHT22 and rain sensor readings received from Arduino.")
        self.g_temp.set_data(self.history["temperature"])
        self.g_hum.set_data(self.history["humidity"])
        self.g_wet.set_data(self.history["wetness"])

    def close(self):
        self.close_serial()
        self.root.destroy()


def main():
    root = tk.Tk()
    WeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
