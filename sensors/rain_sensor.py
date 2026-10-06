"""Digital rain sensor on GPIO17."""
class RainSensor:
    def __init__(self,pin=17):
        self.pin=pin
        import RPi.GPIO as GPIO
        self.GPIO=GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    def is_raining(self):
        # Most LM393 rain modules pull DO LOW when wet.
        return self.GPIO.input(self.pin)==0
    def close(self):
        try: self.GPIO.cleanup(self.pin)
        except Exception: pass
