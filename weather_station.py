import tkinter as tk
import math
from datetime import datetime

from bme280_sensor import BME280Sensor


APP_BG = "#070B10"
PANEL = "#101820"
PANEL_2 = "#141F29"
BORDER = "#263541"
TEXT = "#F3F7FA"
MUTED = "#81909D"
CYAN = "#55D9FF"
GREEN = "#49E58A"
YELLOW = "#FFD34E"
RED = "#FF6675"
PURPLE = "#A98CFF"
BLUE = "#5CA8FF"

MODE = "TEST"
UPDATE_MS = 2000
MAX_POINTS = 90
temperature_history = []
pressure_history = []
humidity_history = []
temperature_min = None
temperature_max = None
last_data = None
last_update = None
active_page = "DASHBOARD"

sensor = BME280Sensor(test_mode=True)


def get_test_data():
    sensor.test_mode = True
    return sensor.read()


def get_live_data():
    sensor.test_mode = False
    return sensor.read()


def clamp(value, low, high):
    return max(low, min(high, value))


def panel(parent, row, column, rowspan=1, columnspan=1):
    frame = tk.Frame(parent, bg=PANEL, highlightthickness=1,
                     highlightbackground=BORDER)
    frame.grid(row=row, column=column, rowspan=rowspan,
               columnspan=columnspan, sticky="nsew", padx=5, pady=5)
    return frame


def title(parent, text, size=11):
    return tk.Label(parent, text=text, bg=PANEL, fg=MUTED,
                    font=("Arial", size, "bold"))


def draw_gauge(canvas, value, minimum, maximum, label, unit, accent, suffix=""):
    canvas.delete("all")
    width = max(150, canvas.winfo_width())
    height = max(130, canvas.winfo_height())
    cx = width / 2
    cy = height * 0.58
    radius = min(width * 0.35, height * 0.38)

    canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius,
                      start=135, extent=-270, style="arc",
                      outline="#263541", width=12)

    if value is not None:
        ratio = clamp((value - minimum) / float(maximum - minimum), 0, 1)
        canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius,
                          start=135, extent=-270 * ratio, style="arc",
                          outline=accent, width=12)

        angle = math.radians(135 - 270 * ratio)
        x = cx + radius * 0.76 * math.cos(angle)
        y = cy - radius * 0.76 * math.sin(angle)
        canvas.create_line(cx, cy, x, y, fill=TEXT, width=3)
        canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5,
                           fill=TEXT, outline="")

        display = f"{value:.1f}{suffix}"
    else:
        display = "--"

    canvas.create_text(cx, cy + 28, text=display, fill=TEXT,
                       font=("Arial", 21, "bold"))
    canvas.create_text(cx, 18, text=label, fill=MUTED,
                       font=("Arial", 10, "bold"))
    canvas.create_text(cx, height - 16,
                       text=f"{minimum:g} — {maximum:g} {unit}",
                       fill="#5F6D78", font=("Arial", 9))


def draw_sparkline(canvas, values, title_text, unit, accent):
    canvas.delete("all")
    width = max(250, canvas.winfo_width())
    height = max(150, canvas.winfo_height())

    canvas.create_text(14, 12, anchor="nw", text=title_text,
                       fill=TEXT, font=("Arial", 12, "bold"))

    if len(values) < 2:
        canvas.create_text(width / 2, height / 2,
                           text="Collecting trend data...",
                           fill=MUTED, font=("Arial", 11))
        return

    low = min(values)
    high = max(values)
    if high == low:
        high += 1
        low -= 1

    left, right, top, bottom = 14, 14, 42, 24
    gw = width - left - right
    gh = height - top - bottom

    for fraction in (0.25, 0.5, 0.75):
        y = top + gh * fraction
        canvas.create_line(left, y, width - right, y,
                           fill="#1D2932", width=1)

    points = []
    for index, value in enumerate(values):
        x = left + index * gw / (len(values) - 1)
        y = top + (high - value) * gh / (high - low)
        points.extend((x, y))

    canvas.create_line(*points, fill=accent, width=3, smooth=True)

    canvas.create_text(width - right, top, anchor="ne",
                       text=f"{high:.1f} {unit}", fill=MUTED,
                       font=("Arial", 9))
    canvas.create_text(width - right, height - 5, anchor="se",
                       text=f"{low:.1f} {unit}", fill="#5F6D78",
                       font=("Arial", 9))

    canvas.create_oval(points[-2] - 4, points[-1] - 4,
                       points[-2] + 4, points[-1] + 4,
                       fill=accent, outline="")


def set_mode(mode):
    global MODE
    MODE = mode
    if MODE == "TEST":
        mode_label.config(text="TEST", fg=YELLOW)
        status_label.config(text="SIMULATION • HARDWARE NOT REQUIRED", fg=YELLOW)
        test_button.config(relief="sunken", bd=3)
        live_button.config(relief="raised", bd=2)
    else:
        mode_label.config(text="LIVE", fg=GREEN)
        status_label.config(text="LIVE SENSOR • BME280", fg=GREEN)
        test_button.config(relief="raised", bd=2)
        live_button.config(relief="sunken", bd=3)
    update_display()


def reset_history():
    global temperature_history, pressure_history, humidity_history
    global temperature_min, temperature_max
    temperature_history = []
    pressure_history = []
    humidity_history = []
    temperature_min = None
    temperature_max = None
    update_display()


def show_page(page):
    global ACTIVE_PAGE
    ACTIVE_PAGE = page
    for name, button in nav_buttons.items():
        button.config(bg="#1E2B35" if name == page else PANEL_2,
                      fg=CYAN if name == page else MUTED)

    if page == "DASHBOARD":
        dashboard_frame.tkraise()
    else:
        analytics_frame.tkraise()


def update_dashboard(data):
    global temperature_min, temperature_max

    temperature = data["temperature"]
    humidity = data["humidity"]
    pressure = data["pressure"]
    altitude = data["altitude"]

    if temperature_min is None:
        temperature_min = temperature
        temperature_max = temperature
    else:
        temperature_min = min(temperature_min, temperature)
        temperature_max = max(temperature_max, temperature)

    temperature_history.append(temperature)
    pressure_history.append(pressure)
    humidity_history.append(humidity)

    if len(temperature_history) > MAX_POINTS:
        temperature_history.pop(0)
        pressure_history.pop(0)
        humidity_history.pop(0)

    temp_value.config(text=f"{temperature:.1f} °C")
    humidity_value.config(text=f"{humidity:.1f} %")
    pressure_value.config(text=f"{pressure:.1f} hPa")
    altitude_value.config(text=f"{altitude:.1f} m")

    temp_range_value.config(
        text=f"{temperature_min:.1f} / {temperature_max:.1f} °C"
    )

    temp_gauge.config(width=250, height=155)
    humidity_gauge.config(width=250, height=155)
    pressure_gauge.config(width=250, height=155)

    draw_gauge(temp_gauge, temperature, 0, 50, "TEMPERATURE", "°C", CYAN)
    draw_gauge(humidity_gauge, humidity, 0, 100, "HUMIDITY", "%", GREEN)
    draw_gauge(pressure_gauge, pressure, 950, 1050, "PRESSURE", "hPa", PURPLE)

    draw_sparkline(temp_chart, temperature_history, "TEMPERATURE TREND", "°C", CYAN)
    draw_sparkline(pressure_chart, pressure_history, "PRESSURE TREND", "hPa", PURPLE)


def update_analytics():
    draw_sparkline(analytics_temp, temperature_history,
                   "TEMPERATURE HISTORY", "°C", CYAN)
    draw_sparkline(analytics_pressure, pressure_history,
                   "PRESSURE HISTORY", "hPa", PURPLE)
    draw_sparkline(analytics_humidity, humidity_history,
                   "HUMIDITY HISTORY", "%", GREEN)

    if temperature_history:
        avg = sum(temperature_history) / len(temperature_history)
        analytics_stats.config(
            text=f"SAMPLES  {len(temperature_history)}    "
                 f"AVG TEMP  {avg:.1f} °C    "
                 f"MIN  {min(temperature_history):.1f} °C    "
                 f"MAX  {max(temperature_history):.1f} °C"
        )
    else:
        analytics_stats.config(text="Waiting for measurements...")


def update_display():
    global last_data, last_update

    if MODE == "TEST":
        data = get_test_data()
        status_label.config(text="SIMULATION • HARDWARE NOT REQUIRED", fg=YELLOW)
        connection_label.config(text="● SYSTEM ONLINE", fg=GREEN)
    else:
        data = get_live_data()
        if not data.get("sensor_ok", False):
            temp_value.config(text="-- °C")
            humidity_value.config(text="-- %")
            pressure_value.config(text="---- hPa")
            altitude_value.config(text="-- m")
            status_label.config(text="LIVE • BME280 NOT CONNECTED", fg=RED)
            connection_label.config(text="● SENSOR OFFLINE", fg=RED)
            sensor_state.config(text="BME280 OFFLINE", fg=RED)
            sensor_detail.config(text="Check I²C wiring and address 0x76 / 0x77")
            last_reading.config(text="No valid reading")
            clock_label.config(text=datetime.now().strftime("%d %b %Y   %H:%M:%S"))
            root.after(UPDATE_MS, update_display)
            return

        status_label.config(text="LIVE • BME280 CONNECTED", fg=GREEN)
        connection_label.config(text="● BME280 ONLINE", fg=GREEN)

    last_data = data
    last_update = datetime.now()

    update_dashboard(data)
    update_analytics()

    sensor_state.config(
        text="BME280 ONLINE" if MODE == "LIVE" else "SIMULATED SENSOR",
        fg=GREEN if MODE == "LIVE" else YELLOW
    )
    sensor_detail.config(
        text="I²C • automatic address scan 0x76 / 0x77"
        if MODE == "LIVE" else "Test generator • safe for exhibition demo"
    )
    last_reading.config(
        text=f"Last sample  {last_update.strftime('%H:%M:%S')}"
    )

    clock_label.config(text=datetime.now().strftime("%d %b %Y   %H:%M:%S"))
    update_counter.config(text=f"REFRESH  {UPDATE_MS // 1000}s")
    root.after(UPDATE_MS, update_display)


def exit_fullscreen(event=None):
    root.attributes("-fullscreen", False)


def enter_fullscreen():
    root.attributes("-fullscreen", True)


def close_app(event=None):
    root.destroy()


root = tk.Tk()
root.title("Smart Weather System — Advanced Station Console")
root.configure(bg=APP_BG)
root.attributes("-fullscreen", True)
root.minsize(900, 600)
root.bind("<Escape>", exit_fullscreen)
root.bind("<F11>", lambda event: enter_fullscreen())
root.bind("<Control-q>", close_app)


# ---------- HEADER ----------
header = tk.Frame(root, bg="#0D141B", height=70)
header.pack(fill="x", padx=6, pady=(6, 2))
header.pack_propagate(False)

brand = tk.Frame(header, bg="#0D141B")
brand.pack(side="left", padx=18)

tk.Label(brand, text="◈", bg="#0D141B", fg=CYAN,
         font=("Arial", 26, "bold")).pack(side="left", padx=(0, 10))
tk.Label(brand, text="SMART WEATHER",
         bg="#0D141B", fg=TEXT,
         font=("Arial", 20, "bold")).pack(anchor="w")
tk.Label(brand, text="ADVANCED STATION CONSOLE",
         bg="#0D141B", fg=MUTED,
         font=("Arial", 8, "bold")).pack(anchor="w")

mode_label = tk.Label(header, text="TEST", bg="#0D141B", fg=YELLOW,
                      font=("Arial", 13, "bold"))
mode_label.pack(side="left", padx=22)

connection_label = tk.Label(header, text="● SYSTEM ONLINE",
                            bg="#0D141B", fg=GREEN,
                            font=("Arial", 11, "bold"))
connection_label.pack(side="left")

clock_label = tk.Label(header, text="", bg="#0D141B", fg=TEXT,
                       font=("Arial", 12, "bold"))
clock_label.pack(side="right", padx=18)


# ---------- NAV ----------
nav = tk.Frame(root, bg=APP_BG)
nav.pack(fill="x", padx=12, pady=3)

nav_buttons = {}
for page in ("DASHBOARD", "ANALYTICS"):
    btn = tk.Button(nav, text=page,
                    command=lambda p=page: show_page(p),
                    bg=PANEL_2, fg=MUTED,
                    activebackground="#24343F",
                    activeforeground=CYAN,
                    font=("Arial", 9, "bold"),
                    bd=0, padx=18, pady=6, cursor="hand2")
    btn.pack(side="left", padx=3)
    nav_buttons[page] = btn

test_button = tk.Button(
    nav, text="TEST MODE",
    command=lambda: set_mode("TEST"),
    bg="#5C4D00", fg=TEXT, activebackground="#806E00",
    font=("Arial", 9, "bold"), bd=0, padx=14, pady=6, cursor="hand2")
test_button.pack(side="right", padx=3)

live_button = tk.Button(
    nav, text="LIVE MODE",
    command=lambda: set_mode("LIVE"),
    bg="#075D31", fg=TEXT, activebackground="#078A48",
    font=("Arial", 9, "bold"), bd=0, padx=14, pady=6, cursor="hand2")
live_button.pack(side="right", padx=3)


status_label = tk.Label(root, text="SIMULATION • HARDWARE NOT REQUIRED",
                        bg=APP_BG, fg=YELLOW,
                        font=("Arial", 9, "bold"))
status_label.pack(pady=1)


# ---------- MAIN STACK ----------
stack = tk.Frame(root, bg=APP_BG)
stack.pack(fill="both", expand=True, padx=8, pady=2)

dashboard_frame = tk.Frame(stack, bg=APP_BG)
analytics_frame = tk.Frame(stack, bg=APP_BG)
dashboard_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
analytics_frame.place(relx=0, rely=0, relwidth=1, relheight=1)


# ---------- DASHBOARD ----------
for col in range(3):
    dashboard_frame.grid_columnconfigure(col, weight=1)
dashboard_frame.grid_rowconfigure(0, weight=0)
dashboard_frame.grid_rowconfigure(1, weight=1)
dashboard_frame.grid_rowconfigure(2, weight=1)

card1 = panel(dashboard_frame, 0, 0)
card2 = panel(dashboard_frame, 0, 1)
card3 = panel(dashboard_frame, 0, 2)

for frame, label_text in ((card1, "TEMPERATURE"), (card2, "HUMIDITY"),
                          (card3, "PRESSURE")):
    title(frame, label_text).pack(anchor="w", padx=12, pady=(8, 0))

temp_value = tk.Label(card1, text="-- °C", bg=PANEL, fg=TEXT,
                      font=("Arial", 23, "bold"))
temp_value.pack(anchor="w", padx=12, pady=(1, 8))

humidity_value = tk.Label(card2, text="-- %", bg=PANEL, fg=TEXT,
                          font=("Arial", 23, "bold"))
humidity_value.pack(anchor="w", padx=12, pady=(1, 8))

pressure_value = tk.Label(card3, text="---- hPa", bg=PANEL, fg=TEXT,
                          font=("Arial", 23, "bold"))
pressure_value.pack(anchor="w", padx=12, pady=(1, 8))


temp_gauge = tk.Canvas(dashboard_frame, bg=PANEL,
                       highlightthickness=1, highlightbackground=BORDER)
humidity_gauge = tk.Canvas(dashboard_frame, bg=PANEL,
                           highlightthickness=1, highlightbackground=BORDER)
pressure_gauge = tk.Canvas(dashboard_frame, bg=PANEL,
                           highlightthickness=1, highlightbackground=BORDER)

temp_gauge.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
humidity_gauge.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
pressure_gauge.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)

temp_chart = tk.Canvas(dashboard_frame, bg=PANEL,
                       highlightthickness=1, highlightbackground=BORDER)
pressure_chart = tk.Canvas(dashboard_frame, bg=PANEL,
                           highlightthickness=1, highlightbackground=BORDER)
info = panel(dashboard_frame, 2, 2)

temp_chart.grid(row=2, column=0, columnspan=1, sticky="nsew", padx=5, pady=5)
pressure_chart.grid(row=2, column=1, columnspan=1, sticky="nsew", padx=5, pady=5)

title(info, "STATION HEALTH").pack(anchor="w", padx=12, pady=(10, 8))

sensor_state = tk.Label(info, text="SIMULATED SENSOR", bg=PANEL,
                        fg=YELLOW, font=("Arial", 14, "bold"))
sensor_state.pack(anchor="w", padx=12)

sensor_detail = tk.Label(info, text="Test generator • safe for exhibition demo",
                         bg=PANEL, fg=MUTED, justify="left",
                         font=("Arial", 9), wraplength=260)
sensor_detail.pack(anchor="w", padx=12, pady=(3, 12))

tk.Label(info, text="TEMPERATURE RANGE", bg=PANEL, fg=MUTED,
         font=("Arial", 9, "bold")).pack(anchor="w", padx=12)
temp_range_value = tk.Label(info, text="-- / -- °C", bg=PANEL, fg=TEXT,
                            font=("Arial", 16, "bold"))
temp_range_value.pack(anchor="w", padx=12, pady=(1, 10))

tk.Label(info, text="ALTITUDE", bg=PANEL, fg=MUTED,
         font=("Arial", 9, "bold")).pack(anchor="w", padx=12)
altitude_value = tk.Label(info, text="-- m", bg=PANEL, fg=TEXT,
                          font=("Arial", 16, "bold"))
altitude_value.pack(anchor="w", padx=12, pady=(1, 10))

tk.Label(info, text="RAIN SENSOR", bg=PANEL, fg=MUTED,
         font=("Arial", 9, "bold")).pack(anchor="w", padx=12)
tk.Label(info, text="NOT CONNECTED", bg=PANEL, fg="#697783",
         font=("Arial", 12, "bold")).pack(anchor="w", padx=12, pady=(1, 10))

last_reading = tk.Label(info, text="Waiting for measurement...",
                        bg=PANEL, fg=MUTED, font=("Arial", 9))
last_reading.pack(anchor="w", padx=12, pady=(4, 10))


# ---------- ANALYTICS ----------
for col in range(2):
    analytics_frame.grid_columnconfigure(col, weight=1)
for row in range(3):
    analytics_frame.grid_rowconfigure(row, weight=1)

analytics_temp = tk.Canvas(analytics_frame, bg=PANEL,
                           highlightthickness=1, highlightbackground=BORDER)
analytics_pressure = tk.Canvas(analytics_frame, bg=PANEL,
                               highlightthickness=1, highlightbackground=BORDER)
analytics_humidity = tk.Canvas(analytics_frame, bg=PANEL,
                               highlightthickness=1, highlightbackground=BORDER)

analytics_temp.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
analytics_pressure.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
analytics_humidity.grid(row=1, column=0, columnspan=2,
                        sticky="nsew", padx=5, pady=5)

analytics_stats = tk.Label(
    analytics_frame,
    text="Waiting for measurements...",
    bg=PANEL_2, fg=TEXT,
    font=("Arial", 11, "bold"))
analytics_stats.grid(row=2, column=0, columnspan=2,
                     sticky="ew", padx=18, pady=8)


# ---------- FOOTER ----------
footer = tk.Frame(root, bg="#0D141B", height=42)
footer.pack(fill="x", padx=6, pady=(2, 6))
footer.pack_propagate(False)

tk.Button(
    footer, text="RESET HISTORY",
    command=reset_history,
    bg=PANEL_2, fg=TEXT, activebackground="#2A3944",
    font=("Arial", 9, "bold"), bd=0, padx=12, pady=5,
    cursor="hand2").pack(side="left", padx=10, pady=5)

tk.Label(footer, text="ESC  EXIT FULLSCREEN   •   F11  FULLSCREEN   •   CTRL+Q  EXIT",
         bg="#0D141B", fg=MUTED,
         font=("Arial", 8, "bold")).pack(side="left", padx=12)

update_counter = tk.Label(footer, text="REFRESH  2s",
                          bg="#0D141B", fg=MUTED,
                          font=("Arial", 8, "bold"))
update_counter.pack(side="right", padx=15)


nav_buttons["DASHBOARD"].config(bg="#1E2B35", fg=CYAN)
dashboard_frame.tkraise()
set_mode("TEST")
root.mainloop()
