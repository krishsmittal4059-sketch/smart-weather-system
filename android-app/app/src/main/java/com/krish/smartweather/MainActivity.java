package com.krish.smartweather;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.*;
import org.json.JSONObject;
import java.io.*;
import java.net.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    EditText ipInput; TextView status,temp,humidity,pressure,altitude,updated;
    Handler handler = new Handler(Looper.getMainLooper());
    ExecutorService executor = Executors.newSingleThreadExecutor();
    Runnable refresh = new Runnable(){ public void run(){ fetchWeather(); handler.postDelayed(this,5000); }};
    @Override public void onCreate(Bundle b){ super.onCreate(b); setContentView(R.layout.activity_main);
        ipInput=findViewById(R.id.ipInput); status=findViewById(R.id.status); temp=findViewById(R.id.temp); humidity=findViewById(R.id.humidity); pressure=findViewById(R.id.pressure); altitude=findViewById(R.id.altitude); updated=findViewById(R.id.updated);
        findViewById(R.id.connectButton).setOnClickListener(v->{ handler.removeCallbacks(refresh); fetchWeather(); handler.postDelayed(refresh,5000); }); }
    void fetchWeather(){ final String ip=ipInput.getText().toString().trim(); if(ip.isEmpty()) return; status.setText("Connecting to Pi..."); executor.execute(()->{ try{
        URL u=new URL("http://"+ip+":5000/api/weather"); HttpURLConnection c=(HttpURLConnection)u.openConnection(); c.setConnectTimeout(3000); c.setReadTimeout(3000); c.setRequestMethod("GET");
        BufferedReader r=new BufferedReader(new InputStreamReader(c.getInputStream())); StringBuilder s=new StringBuilder(); String line; while((line=r.readLine())!=null)s.append(line); r.close(); JSONObject j=new JSONObject(s.toString());
        if(!j.getBoolean("ok")) throw new Exception(j.optString("error","Sensor error"));
        runOnUiThread(()->{ temp.setText("🌡 Temperature: "+j.optDouble("temperature",0)+" °C"); humidity.setText("💧 Humidity: "+j.optDouble("humidity",0)+" %"); pressure.setText("🌬 Pressure: "+j.optDouble("pressure",0)+" hPa"); altitude.setText("⛰ Altitude: "+j.optDouble("altitude",0)+" m"); updated.setText("Last update: "+j.optString("timestamp")); status.setText("● Sensor online"); });
    }catch(Exception e){ runOnUiThread(()->status.setText("● Connection error: "+e.getMessage())); }}); }
    @Override protected void onDestroy(){ handler.removeCallbacks(refresh); executor.shutdownNow(); super.onDestroy(); }
}
