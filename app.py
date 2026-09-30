from flask import Flask, jsonify, render_template
from weather_data import get_weather, set_mode, current_mode

app = Flask(__name__)

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/weather")
def weather():
    return jsonify(get_weather())

@app.get("/api/mode")
def mode_get():
    return jsonify({"ok": True, "mode": current_mode()})

@app.post("/api/mode/<mode>")
def mode_set(mode):
    mode = mode.strip().lower()
    if mode not in ("test", "live"):
        return jsonify({"ok": False, "error": "Mode must be test or live"}), 400
    set_mode(mode)
    return jsonify({"ok": True, "mode": mode})

@app.get("/health")
def health():
    return jsonify({"ok": True, "mode": current_mode()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
