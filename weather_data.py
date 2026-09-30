import math
import time
MODE_FILE = '/opt/smart-weather-system/mode.conf'
def current_mode():
    try:
        with open(MODE_FILE, 'r', encoding='utf-8') as f: mode=f.read().strip().lower()
        return mode if mode in ('test','live') else 'test'
    except OSError: return 'test'
def set_mode(mode):
    with open(MODE_FILE, 'w', encoding='utf-8') as f: f.write(mode)
def test_reading():
    t=time.time()/60.0
    return {'ok':True,'mode':'test','temperature':round(27+1.8*math.sin(t/2),2),'humidity':round(60+5*math.sin(t/3+1),2),'pressure':round(1008+2*math.sin(t/4),2),'altitude':110.0,'timestamp':time.strftime('%Y-%m-%d %H:%M:%S')}
def live_reading():
    import smbus2, bme280
    bus=smbus2.SMBus(1)
    try:
        calibration=bme280.load_calibration_params(bus,0x76)
        data=bme280.sample(bus,0x76,calibration)
        pressure=round(data.pressure,2)
        return {'ok':True,'mode':'live','temperature':round(data.temperature,2),'humidity':round(data.humidity,2),'pressure':pressure,'altitude':round(bme280.bme280.get_altitude(pressure),2),'timestamp':time.strftime('%Y-%m-%d %H:%M:%S')}
    finally: bus.close()
def get_weather():
    if current_mode()=='test': return test_reading()
    try: return live_reading()
    except Exception as e: return {'ok':False,'mode':'live','error':str(e),'timestamp':time.strftime('%Y-%m-%d %H:%M:%S')}
