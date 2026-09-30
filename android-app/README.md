# Smart Weather Android App

This is a lightweight Android app for the Raspberry Pi BME280 weather server.

## How it works

The Pi runs `app.py` on port 5000. The Android app requests `/api/weather` every 5 seconds over the local Wi-Fi network.

## Build

Open the `android-app` folder in Android Studio and build the debug APK.

Install the APK on your Android phone, make sure the phone and Pi are on the same Wi-Fi network, enter the Pi's IP address (for example `192.168.1.100`), and tap Connect.

## Pi side

From the project root on the Pi:

    python3 app.py

The phone then connects to `http://PI-IP:5000/api/weather`.
