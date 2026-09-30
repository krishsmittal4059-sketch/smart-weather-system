from flask import Flask, jsonify, render_template
from bme280_sensor import read_bme280

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/weather")
def weather():
    try:
        return jsonify({"ok": True, **read_bme280()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
