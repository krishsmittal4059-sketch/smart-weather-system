from flask import Flask, jsonify, render_template
from weather_data import get_weather, set_mode

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/weather")
def weather():
    return jsonify(get_weather())

@app.route("/api/mode/<mode>", methods=["POST"])
def mode(mode):
    if mode not in ("test", "live"):
        return jsonify({"ok": False, "error": "Invalid mode"}), 400
    set_mode(mode)
    return jsonify({"ok": True, "mode": mode})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
