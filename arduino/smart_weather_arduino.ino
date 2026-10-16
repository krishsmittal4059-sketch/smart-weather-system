/*
  Smart Weather Observatory - Arduino UNO
  Sensors: DHT22 temperature/humidity module and LM393 rain module.
  BMP180 has been removed from this version.
  USB serial output: readable weather report at 9600 baud.

  Libraries to install in Arduino IDE:
  - DHT sensor library by Adafruit
  - Adafruit Unified Sensor (if requested by Library Manager)

  Check each module's printed VCC/GND labels and voltage requirements
  before powering it. Never power a module that becomes hot.
*/
#include <DHT.h>

#define DHT_PIN 2
#define DHT_TYPE DHT22
#define RAIN_AO_PIN A0
#define RAIN_DO_PIN 3

DHT dht(DHT_PIN, DHT_TYPE);

const int DRY_VALUE = 900;
const int WET_VALUE = 300;

void setup() {
  Serial.begin(9600);
  dht.begin();
  pinMode(RAIN_AO_PIN, INPUT);
  pinMode(RAIN_DO_PIN, INPUT);

  delay(500);
  Serial.println("SMART WEATHER STATION");
  Serial.println("---------------------");
  Serial.println("Sensors initialized!");
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  int rainRaw = analogRead(RAIN_AO_PIN);
  int rainDigital = digitalRead(RAIN_DO_PIN);

  int wetness = map(rainRaw, DRY_VALUE, WET_VALUE, 0, 100);
  wetness = constrain(wetness, 0, 100);

  Serial.println();
  Serial.println("===== WEATHER REPORT =====");

  if (!isnan(temperature) && !isnan(humidity)) {
    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.println(" C");

    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");
  } else {
    Serial.println("DHT22 read error!");
  }

  Serial.print("Rain analog value: ");
  Serial.print(rainRaw);
  Serial.println(" / 1023");

  Serial.print("Estimated plate wetness: ");
  Serial.print(wetness);
  Serial.println(" %");

  Serial.print("Rain threshold output: ");
  Serial.println(rainDigital == LOW ? "TRIGGERED" : "NOT TRIGGERED");

  if (wetness >= 70) {
    Serial.println("Plate status: VERY WET");
  } else if (wetness >= 30) {
    Serial.println("Plate status: DAMP");
  } else {
    Serial.println("Plate status: DRY / LIGHTLY WET");
  }

  Serial.println("==========================");
  delay(1000);
}
