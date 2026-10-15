/*
  Smart Weather Observatory - Arduino UNO
  Sensors: BMP180 (I2C), DHT22 module, LM393 rain module.
  Serial format at 9600 baud:
  WX,tempC,humidityPercent,pressure_hPa,altitude_m,rainWet(0/1)

  Libraries to install in Arduino IDE:
  - Adafruit BMP085 Library (works with BMP180)
  - DHT sensor library by Adafruit
  - Adafruit Unified Sensor

  IMPORTANT: Check each module's VCC/GND labels and voltage requirements
  before powering it. Do not power a board that previously became hot.
*/
#include <Wire.h>
#include <Adafruit_BMP085.h>
#include <DHT.h>

#define DHT_PIN 2
#define DHT_TYPE DHT22
#define RAIN_DO_PIN 3

Adafruit_BMP085 bmp;
DHT dht(DHT_PIN, DHT_TYPE);
bool bmpReady = false;

void setup() {
  Serial.begin(9600);
  Wire.begin();
  pinMode(RAIN_DO_PIN, INPUT);
  dht.begin();
  delay(2000);
  bmpReady = bmp.begin();
  Serial.println("SMART_WEATHER_READY");
}

void loop() {
  float humidity = dht.readHumidity();
  float dhtTempC = dht.readTemperature();
  int rainWet = (digitalRead(RAIN_DO_PIN) == LOW) ? 1 : 0;

  // Use BMP180 temperature when available; otherwise use DHT22 temperature.
  float temperatureC = isnan(dhtTempC) ? -999.0 : dhtTempC;
  float pressureHpa = -1.0;
  float altitudeM = -999.0;

  if (bmpReady) {
    temperatureC = bmp.readTemperature();
    pressureHpa = bmp.readPressure() / 100.0;
    altitudeM = bmp.readAltitude();
  }

  if (isnan(humidity)) {
    Serial.println("ERROR,DHT22");
  } else if (bmpReady) {
    Serial.print("WX,");
    Serial.print(temperatureC, 1);
    Serial.print(",");
    Serial.print(humidity, 1);
    Serial.print(",");
    Serial.print(pressureHpa, 1);
    Serial.print(",");
    Serial.print(altitudeM, 1);
    Serial.print(",");
    Serial.println(rainWet);
  } else {
    // Explicitly mark unavailable BMP180 readings; dashboard reports error.
    Serial.print("WX,");
    Serial.print(temperatureC, 1);
    Serial.print(",");
    Serial.print(humidity, 1);
    Serial.println(",-1,-999,0");
  }
  delay(2000);
}
