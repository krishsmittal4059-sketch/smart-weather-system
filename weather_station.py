import tkinter as tk
from datetime import datetime

from bme280_sensor import BME280Sensor


MODE = "TEST"
UPDATE_MS = 2000
MAX_POINTS = 60

temperature_history = []
pressure_history = []
temperature_min = None
temperature_max = None
test_time = 0


sensor = BME280Sensor(test_mode=True)


def get_test_data():
    sensor.test_mode = True
    return sensor.read()


def get_live_data():
    sensor.test_mode = False
    return sensor.read()


def draw_graph(canvas, values, title, unit, line_color):
    canvas.delete("all")
    width = canvas.winfo_width()
    height = canvas.winfo_height()

    canvas.create_rectangle(0, 0, width, height, fill="#111820", outline="")
    canvas.create_text(18, 15, anchor="nw", text=title,
                       fill="white", font=("Arial", 15, "bold"))

    if len(values) < 2:
        canvas.create_text(width / 2, height / 2,
                           text="Collecting data...",
                           fill="#82909C", font=("Arial", 13))
        return

    minimum = min(values)
    maximum = max(values)
    if maximum == minimum:
        maximum += 1
        minimum -= 1

    left = 48
    right = 18
    top = 48
    bottom = 28
    graph_width = max(1, width - left - right)
    graph_height = max(1, height - top - bottom)

    # Lightweight grid
    for fraction in (0.25, 0.5, 0.75):
        y = top + fraction * graph_height
        canvas.create_line(left, y, width - right, y,
                           fill="#26323C", width=1)

    points = []
    for i, value in enumerate(values):
        x = left + (i / (len(values) - 1)) * graph_width
        y = top + ((maximum - value) / (maximum - minimum)) * graph_height
        points.extend([x, y])

    canvas.create_line(*points, fill=line_color, width=3, smooth=True)

    canvas.create_text(width - right, top, anchor="ne",
                       text=f"{maximum:.1f} {unit}", fill="#DCE6ED",
                       font=("Arial", 10))
    canvas.create_text(width - right, height - bottom, anchor="se",
                       text=f"{minimum:.1f} {unit}", fill="#82909C",
                       font=("Arial", 10))


def card(parent, title, initial, column):
    frame = tk.Frame(parent, bg="#111820", highlightthickness=1,
                     highlightbackground="#26323C")
    frame.grid(row=0, column=column, sticky="nsew", padx=5)
    tk.Label(frame, text=title, bg="#111820", fg="#82909C",
             font=("Arial", 11, "bold")).pack(pady=(10, 2))
    value = tk.Label(frame, text=initial, bg="#111820", fg="white",
                     font=("Arial", 24, "bold"))
    value.pack(pady=(0, 10))
    return value


def set_mode(mode):
    global MODE
    MODE = mode

    if MODE == "TEST":
        mode_label.config(text="● TEST MODE", fg="#FFD34E")
        status_label.config(text="SIMULATION • NO SENSOR REQUIRED", fg="#FFD34E")
        test_button.config(relief="sunken", bd=4)
        live_button.config(relief="raised", bd=2)
    else:
        mode_label.config(text="● LIVE MODE", fg="#49E58A")
        status_label.config(text="CONNECTING TO BME280...", fg="#49E58A")
        test_button.config(relief="raised", bd=2)
        live_button.config(relief="sunken", bd=4)

    update_display()


def reset_min_max():
    global temperature_min, temperature_max
    temperature_min = None
    temperature_max = None
    minmax_label.config(text="Temperature range: -- / -- °C")


def update_display():
    global temperature_min, temperature_max

    if MODE == "TEST":
        sensor.test_mode = True
        data = sensor.read()
        temperature = data["temperature"]
        humidity = data["humidity"]
        pressure = data["pressure"]
        altitude = data["altitude"]
        rain = False
        status_label.config(text="SIMULATION • NO SENSOR REQUIRED", fg="#FFD34E")
        connection_label.config(text="● SYSTEM ONLINE", fg="#49E58A")
    else:
        data = get_live_data()
        if not data.get("sensor_ok", False):
            temperature_label.config(text="-- °C")
            humidity_label.config(text="-- %")
            pressure_label.config(text="---- hPa")
            altitude_label.config(text="-- m")
            rain_label.config(text="RAIN SENSOR: NOT CONNECTED", fg="#FF7070")
            status_label.config(text="LIVE MODE • BME280 NOT CONNECTED", fg="#FF7070")
            connection_label.config(text="● SENSOR OFFLINE", fg="#FF7070")
            time_label.config(text=datetime.now().strftime("%d-%m-%Y   %H:%M:%S"))
            next_update_label.config(text="Waiting for sensor...")
            root.after(UPDATE_MS, update_display)
            return

        temperature = data["temperature"]
        humidity = data["humidity"]
        pressure = data["pressure"]
        altitude = data["altitude"]
        connection_label.config(text="● BME280 ONLINE", fg="#49E58A")

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
        text=f"Temperature range: {temperature_min:.1f} / {temperature_max:.1f} °C"
    )

    rain_label.config(text="RAIN SENSOR: NOT CONNECTED", fg="#82909C")

    time_label.config(text=datetime.now().strftime("%d-%m-%Y   %H:%M:%S"))
    next_update_label.config(text=f"Auto refresh: {UPDATE_MS // 1000}s")

    draw_graph(temperature_graph, temperature_history,
               "TEMPERATURE", "°C", "#55D9FF")
    draw_graph(pressure_graph, pressure_history,
               "PRESSURE", "hPa", "#A98CFF")

    root.after(UPDATE_MS, update_display)


def exit_fullscreen(event=None):
    root.attributes("-fullscreen", False)


def close_app(event=None):
    root.destroy()


root = tk.Tk()
root.title("Smart Weather System")
root.configure(bg="#080D12")
root.attributes("-fullscreen", True)
root.bind("<Escape>", exit_fullscreen)
root.bind("<Control-q>", close_app)

# Header
header = tk.Frame(root, bg="#10161D")
header.pack(fill="x", padx=6, pady=(6, 3))

tk.Label(header, text="SMART WEATHER SYSTEM",
         bg="#10161D", fg="white",
         font=("Arial", 24, "bold")).pack(side="left", padx=18, pady=10)

mode_label = tk.Label(header, text="● TEST MODE",
                      bg="#10161D", fg="#FFD34E",
                      font=("Arial", 15, "bold"))
mode_label.pack(side="left", padx=10)

connection_label = tk.Label(header, text="● SYSTEM ONLINE",
                            bg="#10161D", fg="#49E58A",
                            font=("Arial", 12, "bold"))
connection_label.pack(side="left", padx=10)

button_frame = tk.Frame(header, bg="#10161D")
button_frame.pack(side="right", padx=12, pady=5)

test_button = tk.Button(
    button_frame, text="TEST",
    command=lambda: set_mode("TEST"),
    font=("Arial", 13, "bold"),
    bg="#665500", fg="white",
    activebackground="#8A7300", activeforeground="white",
    width=9, height=1, relief="sunken", bd=4, cursor="hand2")
test_button.pack(side="left", padx=4)

live_button = tk.Button(
    button_frame, text="LIVE",
    command=lambda: set_mode("LIVE"),
    font=("Arial", 13, "bold"),
    bg="#087A3B", fg="white",
    activebackground="#0BAA55", activeforeground="white",
    width=9, height=1, relief="raised", bd=2, cursor="hand2")
live_button.pack(side="left", padx=4)

# Status bar
status_label = tk.Label(
    root, text="SIMULATION • NO SENSOR REQUIRED",
    bg="#080D12", fg="#FFD34E",
    font=("Arial", 11, "bold"))
status_label.pack(pady=(2, 2))

# Measurement cards
values_frame = tk.Frame(root, bg="#080D12")
values_frame.pack(fill="x", padx=8, pady=4)

for i in range(4):
    values_frame.grid_columnconfigure(i, weight=1)

temperature_label = card(values_frame, "TEMPERATURE", "-- °C", 0)
humidity_label = card(values_frame, "HUMIDITY", "-- %", 1)
pressure_label = card(values_frame, "PRESSURE", "---- hPa", 2)
altitude_label = card(values_frame, "ALTITUDE", "-- m", 3)

# Secondary information
info_frame = tk.Frame(root, bg="#080D12")
info_frame.pack(fill="x", padx=14, pady=4)

minmax_label = tk.Label(
    info_frame, text="Temperature range: -- / -- °C",
    bg="#080D12", fg="#DCE6ED",
    font=("Arial", 12, "bold"))
minmax_label.pack(side="left")

rain_label = tk.Label(
    info_frame, text="RAIN SENSOR: NOT CONNECTED",
    bg="#080D12", fg="#DCE6ED",
    font=("Arial", 12, "bold"))
rain_label.pack(side="right")

# Graphs
graphs = tk.Frame(root, bg="#080D12")
graphs.pack(fill="both", expand=True, padx=10, pady=4)

temperature_graph = tk.Canvas(
    graphs, bg="#111820", highlightthickness=1,
    highlightbackground="#26323C")
temperature_graph.pack(side="left", fill="both", expand=True, padx=4)

pressure_graph = tk.Canvas(
    graphs, bg="#111820", highlightthickness=1,
    highlightbackground="#26323C")
pressure_graph.pack(side="right", fill="both", expand=True, padx=4)

# Footer
footer = tk.Frame(root, bg="#10161D")
footer.pack(fill="x", padx=6, pady=(3, 6))

reset_button = tk.Button(
    footer, text="RESET MIN / MAX",
    command=reset_min_max,
    font=("Arial", 10, "bold"),
    bg="#27313A", fg="white",
    activebackground="#3A4650", activeforeground="white",
    padx=12, pady=4, cursor="hand2")
reset_button.pack(side="left", padx=10, pady=5)

time_label = tk.Label(
    footer, text="", bg="#10161D", fg="#AAB6BF",
    font=("Arial", 11))
time_label.pack(side="left", padx=15)

next_update_label = tk.Label(
    footer, text="Auto refresh: 2s", bg="#10161D", fg="#82909C",
    font=("Arial", 10))
next_update_label.pack(side="right", padx=15)

set_mode("TEST")
root.mainloop()
