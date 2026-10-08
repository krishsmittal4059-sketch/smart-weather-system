"""DHT11 reader using Adafruit's lightweight DHT library."""
class DHT11:
    def __init__(self, pin=4):
        self.pin = pin
        self.sensor = None
        self.module = None
        try:
            import Adafruit_DHT
            self.module = Adafruit_DHT
            self.sensor = Adafruit_DHT.DHT11
        except Exception as exc:
            self.error = str(exc)

    def read(self):
        if self.module is None:
            raise RuntimeError("Adafruit_DHT is not installed")
        humidity, temperature = self.module.read_retry(
            self.sensor, self.pin, retries=2, delay_seconds=1
        )
        if humidity is None or temperature is None:
            raise RuntimeError("DHT11 did not return a reading")
        return {
            "temperature": round(float(temperature), 1),
            "humidity": round(float(humidity), 1),
        }
