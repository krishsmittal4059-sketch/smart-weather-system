import tkinter as tk
import random
import math
from datetime import datetime

MODE = "TEST"
UPDATE_MS = 2000
MAX_POINTS = 60

temperature_history = []
pressure_history = []
temperature_min = None
temperature_max = None
test_time = 0


def get_test_data():
    global test_time
    test_time += 1
    temperature = 28 + 3 * math.sin(test_time / 8) + random.uniform(-0.3, 0.3)
    humidity = 60 + 12 * math.sin(test_time / 10) + random.uniform(-1, 1)
    pressure = 1008 + 5 * math.sin(test_time / 15) + random.uniform(-0.5, 0.5)
    altitude = 120 + random.uniform(-1, 1)
    rain = random.random() < 0.08
    return temperature, humidity, pressure, altitude, rain


def get_live_data():
    # BME280 support will be connected here when the sensor is available.
    return None


def draw_graph(canvas, values, title, unit):
    canvas.delete("all")
    width = canvas.winfo_width()
    height = canvas.winfo_height()
    if width < 10 or height < 10:
        return

    canvas.create_rectangle(0, 0, width, height, fill="#101010", outline="")
    canvas.create_text(15, 15, anchor="nw", text=title,
                       fill="white", font=("Arial", 14, "bold"))

    if len(values) < 2:
        canvas.create_text(width / 2, height / 2,
                           text="Waiting for data...",
                           fill="#888888", font=("Arial", 12))
        return

    minimum = min(values)
    maximum = max(values)
    if maximum == minimum:
        maximum += 1
        minimum -= 1

    margin = 35
    graph_width = width - 2 * margin
    graph_height = height - 2 * margin
    points = []

    for i, value in enumerate(values):
        x = margin + (i / (len(values) - 1)) * graph_width
        y = margin + ((maximum - value) / (maximum - minimum)) * graph_height
        points.extend([x, y])

    canvas.create_line(*points, fill="#00FFFF", width=3, smooth=True)
    canvas.create_text(width - 10, margin, anchor="ne",
                       text=f"{maximum:.1f} {unit}", fill="white")
    canvas.create_text(width - 10, height - margin, anchor="se",
                       text=f"{minimum:.1f} {unit}", fill="white")


def set_mode(mode):
    global MODE
    MODE = mode

    if MODE == "TEST":
        mode_label.config(text="● TEST MODE", fg="#FFD700")
        status_label.config(text="SIMULATION DATA — NO SENSOR REQUIRED",
                            fg="#FFD700")
        test_button.config(relief="sunken", bd=5)
        live_button.config(relief="raised", bd=3)
    else:
        mode_label.config(text="● LIVE MODE", fg="#00FF66")
        test_button.config(relief="raised", bd=3)
        live_button.config(relief="sunken", bd=5)

    update_display()


def reset_min_max():
    global temperature_min, temperature_max
    temperature_min = None
    temperature_max = None
    minmax_label.config(text="MIN: -- °C       MAX: -- °C")


def update_display():
    global temperature_min, temperature_max

    if MODE == "TEST":
        temperature, humidity, pressure, altitude, rain = get_test_data()
        status_label.config(text="SIMULATION DATA — NO SENSOR REQUIRED",
                            fg="#FFD700")
    else:
        data = get_live_data()

        if data is None:
            temperature_label.config(text="-- °C")
            humidity_label.config(text="-- %")
            pressure_label.config(text="---- hPa")
            altitude_label.config(text="-- m")
            rain_label.config(text="RAIN: SENSOR NOT CONNECTED",
                              fg="#FF5555")
            status_label.config(text="LIVE MODE — BME280 NOT CONNECTED",
                                fg="#FF5555")
            time_label.config(text=datetime.now().strftime("%d-%m-%Y   %H:%M:%S"))
            root.after(UPDATE_MS, update_display)
            return

        temperature, humidity, pressure, altitude, rain = data

    if temperature_min is None:
        temperature_min = temperature
        temperature_max = temperature
    else:
        temperature_min = min(temperature_min, temperature)
        temperature_max = max(temperature_max, temperature)

    temperature_history.append(temperature)
    pressure_history.append(pressure)

    if len(temperature_history) > MAX_POINTS:
        temperature_history.pop(0)
    if len(pressure_history) > MAX_POINTS:
        pressure_history.pop(0)

    temperature_label.config(text=f"{temperature:.1f} °C")
    humidity_label.config(text=f"{humidity:.1f} %")
    pressure_label.config(text=f"{pressure:.1f} hPa")
    altitude_label.config(text=f"{altitude:.1f} m")

    minmax_label.config(
        text=f"MIN: {temperature_min:.1f} °C       MAX: {temperature_max:.1f} °C"
    )

    if rain:
        rain_label.config(text="☔ RAIN: YES", fg="#00FFFF")
    else:
        rain_label.config(text="☀ RAIN: NO", fg="white")

    time_label.config(text=datetime.now().strftime("%d-%m-%Y   %H:%M:%S"))

    draw_graph(temperature_graph, temperature_history, "TEMPERATURE", "°C")
    draw_graph(pressure_graph, pressure_history, "PRESSURE", "hPa")

    root.after(UPDATE_MS, update_display)


def exit_fullscreen(event=None):
    root.attributes("-fullscreen", False)


root = tk.Tk()
root.title("Raspberry Pi Weather Station")
root.configure(bg="#050505")
root.attributes("-fullscreen", True)
root.bind("<Escape>", exit_fullscreen)

top = tk.Frame(root, bg="#151515")
top.pack(fill="x", padx=5, pady=5)

title_label = tk.Label(top, text="WEATHER STATION",
                       bg="#151515", fg="white",
                       font=("Arial", 24, "bold"))
title_label.pack(side="left", padx=20, pady=10)

mode_label = tk.Label(top, text="● TEST MODE",
                      bg="#151515", fg="#FFD700",
                      font=("Arial", 18, "bold"))
mode_label.pack(side="left", padx=15)

button_frame = tk.Frame(top, bg="#151515")
button_frame.pack(side="right", padx=15, pady=5)

test_button = tk.Button(
    button_frame, text="TEST MODE",
    command=lambda: set_mode("TEST"),
    font=("Arial", 16, "bold"),
    bg="#806600", fg="white",
    activebackground="#B38F00",
    activeforeground="white",
    width=14, height=2,
    relief="sunken", bd=5, cursor="hand2")
test_button.pack(side="left", padx=5)

live_button = tk.Button(
    button_frame, text="LIVE MODE",
    command=lambda: set_mode("LIVE"),
    font=("Arial", 16, "bold"),
    bg="#087A3B", fg="white",
    activebackground="#0BAA55",
    activeforeground="white",
    width=14, height=2,
    relief="raised", bd=3, cursor="hand2")
live_button.pack(side="left", padx=5)

status_label = tk.Label(
    root, text="SIMULATION DATA — NO SENSOR REQUIRED",
    bg="#050505", fg="#FFD700",
    font=("Arial", 13, "bold"))
status_label.pack(pady=3)

values_frame = tk.Frame(root, bg="#050505")
values_frame.pack(fill="x", padx=10, pady=5)

temperature_label = tk.Label(
    values_frame, text="-- °C", bg="#050505", fg="white",
    font=("Arial", 32, "bold"))
temperature_label.grid(row=0, column=0, padx=25)

humidity_label = tk.Label(
    values_frame, text="-- %", bg="#050505", fg="white",
    font=("Arial", 26, "bold"))
humidity_label.grid(row=0, column=1, padx=25)

pressure_label = tk.Label(
    values_frame, text="---- hPa", bg="#050505", fg="white",
    font=("Arial", 26, "bold"))
pressure_label.grid(row=0, column=2, padx=25)

altitude_label = tk.Label(
    values_frame, text="-- m", bg="#050505", fg="white",
    font=("Arial", 26, "bold"))
altitude_label.grid(row=0, column=3, padx=25)

minmax_label = tk.Label(
    root, text="MIN: -- °C       MAX: -- °C",
    bg="#050505", fg="white",
    font=("Arial", 15, "bold"))
minmax_label.pack(pady=4)

rain_label = tk.Label(
    root, text="☀ RAIN: NO",
    bg="#050505", fg="white",
    font=("Arial", 17, "bold"))
rain_label.pack(pady=3)

reset_button = tk.Button(
    root, text="RESET MIN / MAX",
    command=reset_min_max,
    font=("Arial", 11, "bold"),
    bg="#333333", fg="white",
    activebackground="#555555",
    activeforeground="white",
    padx=15, pady=5, cursor="hand2")
reset_button.pack(pady=3)

graphs = tk.Frame(root, bg="#050505")
graphs.pack(fill="both", expand=True, padx=10, pady=5)

temperature_graph = tk.Canvas(
    graphs, bg="#101010", highlightthickness=1,
    highlightbackground="#333333")
temperature_graph.pack(side="left", fill="both", expand=True, padx=5)

pressure_graph = tk.Canvas(
    graphs, bg="#101010", highlightthickness=1,
    highlightbackground="#333333")
pressure_graph.pack(side="right", fill="both", expand=True, padx=5)

time_label = tk.Label(
    root, text="", bg="#050505", fg="#888888",
    font=("Arial", 12))
time_label.pack(pady=4)

set_mode("TEST")
root.mainloop()
