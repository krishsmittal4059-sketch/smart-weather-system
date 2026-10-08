#!/usr/bin/env python3
"""RPi Weather Observatory - lightweight Tkinter dashboard for Pi 1 B+."""
import math, random, sys, tkinter as tk
from collections import deque
from datetime import datetime

UPDATE_MS=2500
MAX_POINTS=90
BG="#071922"; HEADER="#0e2430"; PANEL="#122b39"; PANEL2="#1a3647"
BORDER="#2d4d5d"; GRID="#213f4c"; TEXT="#edf7fb"; MUTED="#9ab5c0"
CYAN="#5ad7ff"; GREEN="#69e69a"; YELLOW="#ffd166"; RED="#ff6b6b"; PURPLE="#9d8cff"

class HistoryGraph(tk.Canvas):
    def __init__(self,parent,title,unit,accent):
        super().__init__(parent,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        self.title,self.unit,self.accent=title,unit,accent; self.values=[]
        self.bind("<Configure>",self.redraw)
    def set_data(self,values): self.values=list(values); self.redraw()
    def redraw(self,event=None):
        w,h=self.winfo_width(),self.winfo_height()
        if w<30 or h<30:return
        self.delete("all"); l,r,t,b=24,12,28,18; cw,ch=w-l-r,h-t-b
        self.create_text(12,8,anchor="nw",text=self.title,fill=TEXT,font=("Helvetica",11,"bold"))
        for q in (.25,.5,.75):
            y=t+ch*q; self.create_line(l,y,w-r,y,fill=GRID)
        if not self.values:
            self.create_text(w/2,h/2,text="Waiting for readings...",fill=MUTED,font=("Helvetica",10)); return
        lo,hi=min(self.values),max(self.values)
        if lo==hi: lo-=1; hi+=1
        pad=max((hi-lo)*.1,.01); lo-=pad; hi+=pad
        pts=[]
        for i,v in enumerate(self.values):
            x=l+(i/max(1,len(self.values)-1))*cw
            y=t+ch-(v-lo)/(hi-lo)*ch; pts += [x,y]
        if len(pts)>=4:
            self.create_line(*pts,fill=self.accent,width=2,smooth=True)
            x,y=pts[-2:]; self.create_oval(x-3,y-3,x+3,y+3,fill=self.accent,outline=self.accent)
        self.create_text(w-8,9,anchor="ne",text=f"{max(self.values):.1f}{self.unit}",fill=MUTED,font=("Helvetica",9))

class WeatherApp:
    def __init__(self,root):
        self.root=root; self.mode="TEST"; self.fullscreen="--windowed" not in sys.argv
        self.history={k:deque(maxlen=MAX_POINTS) for k in ("temperature","humidity","pressure")}
        self.temp_min=self.temp_max=None; self.latest={}; self.sim={"temperature":26.0,"humidity":60.0,"pressure":1012.0}
        self.bme=self.dht=self.rtc=self.rain=None
        try:
            from sensors.oled import OLEDDisplay
            self.oled=OLEDDisplay()
        except Exception:
            self.oled=None
        root.title("RPi Weather Observatory"); root.configure(bg=BG); root.minsize(980,620); root.geometry("1280x780")
        root.bind("<F11>",lambda e:self.set_fullscreen(not self.fullscreen)); root.bind("<Escape>",lambda e:self.set_fullscreen(False))
        self.build_ui(); self.set_fullscreen(self.fullscreen); self.sample()

    def build_ui(self):
        top=tk.Frame(self.root,bg=HEADER,height=76); top.pack(fill="x",padx=10,pady=(10,6)); top.pack_propagate(False)
        tk.Label(top,text="◌  RPi Weather Observatory",bg=HEADER,fg=TEXT,font=("Helvetica",22,"bold")).pack(side="left",padx=18,pady=18)
        controls=tk.Frame(top,bg=HEADER); controls.pack(side="right",padx=12)
        self.mode_btn=tk.Button(controls,text="LIVE MODE",command=self.toggle_mode,bg="#1b4c5f",fg=TEXT,bd=0,padx=12,pady=8,font=("Helvetica",10,"bold")); self.mode_btn.pack(side="left",padx=3)
        for text,cmd in (("FULL SCREEN",lambda:self.set_fullscreen(True)),("WINDOWED",lambda:self.set_fullscreen(False)),("RESET HISTORY",self.clear_history),("EXIT",self.root.destroy)):
            tk.Button(controls,text=text,command=cmd,bg=PANEL2 if text!="EXIT" else "#5a2d2d",fg=TEXT,bd=0,padx=10,pady=8,font=("Helvetica",10,"bold")).pack(side="left",padx=3)
        self.status=tk.Label(self.root,text="TEST MODE • Simulation active",bg=BG,fg=YELLOW,font=("Helvetica",10,"bold")); self.status.pack(anchor="w",padx=12,pady=(0,6))
        body=tk.Frame(self.root,bg=BG); body.pack(fill="both",expand=True,padx=10)
        cards=tk.Frame(body,bg=BG); cards.pack(fill="x",pady=(0,8))
        self.metric={}
        for i,(name,unit,accent) in enumerate((("Temperature","°C",CYAN),("Humidity","%",GREEN),("Pressure","hPa",PURPLE),("Altitude","m",YELLOW))):
            c=tk.Frame(cards,bg=PANEL,highlightthickness=1,highlightbackground=BORDER,padx=14,pady=12); c.pack(side="left",fill="x",expand=True,padx=(0 if i==0 else 6,0))
            tk.Label(c,text=name,bg=PANEL,fg=MUTED,font=("Helvetica",10,"bold")).pack(anchor="w")
            v=tk.Label(c,text="--",bg=PANEL,fg=accent,font=("Helvetica",28,"bold")); v.pack(anchor="w",pady=(5,0)); self.metric[name]=v
        lower=tk.Frame(body,bg=BG); lower.pack(fill="both",expand=True)
        charts=tk.Frame(lower,bg=BG); charts.pack(side="left",fill="both",expand=True)
        self.g_temp=HistoryGraph(charts,"TEMPERATURE HISTORY"," °C",CYAN); self.g_temp.pack(fill="both",expand=True,padx=(0,6),pady=(0,6))
        self.g_hum=HistoryGraph(charts,"HUMIDITY HISTORY"," %",GREEN); self.g_hum.pack(fill="both",expand=True,padx=(0,6),pady=(0,6))
        self.g_press=HistoryGraph(charts,"PRESSURE HISTORY"," hPa",PURPLE); self.g_press.pack(fill="both",expand=True,padx=(0,6))
        side=tk.Frame(lower,bg=BG,width=340); side.pack(side="right",fill="y"); side.pack_propagate(False)
        info=tk.Frame(side,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); info.pack(fill="both",expand=True)
        self.fields={}
        for key,label in (("system","SYSTEM STATUS"),("mode","OPERATING MODE"),("rain","RAIN SENSOR"),("clock","RTC TIME"),("range","TEMPERATURE RANGE"),("sensors","SENSORS")):
            tk.Label(info,text=label,bg=PANEL,fg=MUTED,font=("Helvetica",10,"bold")).pack(anchor="w",padx=16,pady=(10,2))
            v=tk.Label(info,text="--",bg=PANEL,fg=TEXT,font=("Helvetica",13,"bold"),wraplength=300,justify="left"); v.pack(anchor="w",padx=16,pady=(0,5)); self.fields[key]=v
        self.detail=tk.Label(side,text="TEST mode works without hardware.",bg=PANEL2,fg=TEXT,wraplength=300,justify="left",font=("Helvetica",10),padx=12,pady=10); self.detail.pack(fill="x",pady=(8,0))

    def set_fullscreen(self,value): self.fullscreen=bool(value); self.root.attributes("-fullscreen",self.fullscreen)
    def toggle_mode(self): self.set_mode("LIVE" if self.mode=="TEST" else "TEST")
    def set_mode(self,mode):
        self.mode=mode; self.mode_btn.config(text="TEST MODE" if mode=="LIVE" else "LIVE MODE")
        self.status.config(text=("LIVE MODE • Reading BME280 + DHT11 + DS3231 + rain sensor" if mode=="LIVE" else "TEST MODE • Simulation active"),fg=GREEN if mode=="LIVE" else YELLOW)
        self.clear_history()

    def clear_history(self):
        for v in self.history.values(): v.clear()
        self.temp_min=self.temp_max=None; self.redraw()

    def init_live(self):
        if self.bme is None:
            from sensors.bme280 import BME280
            self.bme=BME280()
        if self.dht is None:
            from sensors.dht11 import DHT11
            self.dht=DHT11()
        if self.rtc is None:
            from sensors.ds3231 import DS3231
            self.rtc=DS3231()
        if self.rain is None:
            from sensors.rain_sensor import RainSensor
            self.rain=RainSensor()

    def read_live(self):
        result={"sensor_ok":False,"rain":False,"mode":"LIVE","errors":[]}
        try:
            if self.bme is None:
                from sensors.bme280 import BME280
                self.bme=BME280()
            result.update(self.bme.read())
            result["sensor_ok"]=True
        except Exception as e:
            result["errors"].append("BME280: "+str(e))
        try:
            if self.dht is None:
                from sensors.dht11 import DHT11
                self.dht=DHT11()
            d=self.dht.read()
            result["dht_humidity"]=d["humidity"]
            result["dht_temperature"]=d["temperature"]
        except Exception as e:
            result["errors"].append("DHT11: "+str(e))
        try:
            if self.rtc is None:
                from sensors.ds3231 import DS3231
                self.rtc=DS3231()
            result["rtc"]=self.rtc.read_datetime()
        except Exception as e:
            result["errors"].append("DS3231: "+str(e))
        try:
            if self.rain is None:
                from sensors.rain_sensor import RainSensor
                self.rain=RainSensor()
            result["rain"]=self.rain.is_raining()
        except Exception as e:
            result["errors"].append("RAIN: "+str(e))
        return result

    def read_test(self):
        self.sim["temperature"]=max(18,min(40,self.sim["temperature"]+random.uniform(-.25,.25)))
        self.sim["humidity"]=max(25,min(90,self.sim["humidity"]+random.uniform(-.8,.8)))
        self.sim["pressure"]=max(980,min(1030,self.sim["pressure"]+random.uniform(-.6,.6)))
        alt=44330*(1-(self.sim["pressure"]/1013.25)**.1903)
        return {"temperature":round(self.sim["temperature"],1),"humidity":round(self.sim["humidity"],1),"pressure":round(self.sim["pressure"],1),"altitude":round(alt,1),"rain":random.random()<.03,"sensor_ok":True,"mode":"TEST","rtc":datetime.now(),"errors":[]}

    def sample(self):
        data=self.read_test() if self.mode=="TEST" else self.read_live(); self.latest=data
        vals={}
        for k in ("temperature","humidity","pressure"):
            try: vals[k]=float(data[k])
            except (KeyError,TypeError,ValueError): vals[k]=None
        if vals["temperature"] is not None:
            self.history["temperature"].append(vals["temperature"]); self.temp_min=vals["temperature"] if self.temp_min is None else min(self.temp_min,vals["temperature"]); self.temp_max=vals["temperature"] if self.temp_max is None else max(self.temp_max,vals["temperature"])
        for k in ("humidity","pressure"):
            if vals[k] is not None:self.history[k].append(vals[k])
        self.redraw(); self.root.after(UPDATE_MS,self.sample)

    def redraw(self):
        d=self.latest
        for key,data_key,fmt in (("Temperature","temperature","{:.1f}"),("Humidity","humidity","{:.1f}"),("Pressure","pressure","{:.1f}"),("Altitude","altitude","{:.1f}")):
            val=d.get(data_key); self.metric[key].config(text=fmt.format(float(val)) if val is not None else "--")
        rtc=d.get("rtc"); self.fields["clock"].config(text=rtc.strftime("%Y-%m-%d  %H:%M:%S") if hasattr(rtc,"strftime") else "--")
        self.fields["mode"].config(text=self.mode,fg=GREEN if self.mode=="LIVE" else YELLOW)
        self.fields["rain"].config(text="RAIN DETECTED" if d.get("rain") else "DRY",fg=YELLOW if d.get("rain") else GREEN)
        self.fields["range"].config(text=f"{self.temp_min:.1f} °C  /  {self.temp_max:.1f} °C" if self.temp_min is not None else "--")
        if self.mode=="TEST":
            self.fields["system"].config(text="SIMULATION READY",fg=YELLOW); self.fields["sensors"].config(text="TEST DATA")
            self.detail.config(text="Simulation active. No sensors are required. Switch to LIVE when hardware is connected.")
        else:
            errs=d.get("errors",[]); self.fields["system"].config(text="LIVE • OK" if d.get("sensor_ok") else "LIVE • SENSOR ERROR",fg=GREEN if d.get("sensor_ok") else RED)
            self.fields["sensors"].config(text="\n".join(("✓ "+x.split(":")[0] if ":" in x else x) for x in errs) if errs else "✓ BME280\n✓ DHT11\n✓ DS3231\n✓ Rain sensor")
            self.detail.config(text="; ".join(errs) if errs else "All requested sensors are responding.")
        if self.oled is not None:
            self.oled.show(temperature=d.get("temperature"),humidity=d.get("humidity"),pressure=d.get("pressure"),rain=d.get("rain",False),clock=rtc,mode=self.mode)
        self.g_temp.set_data(self.history["temperature"]); self.g_hum.set_data(self.history["humidity"]); self.g_press.set_data(self.history["pressure"])

def main():
    root=tk.Tk(); WeatherApp(root); root.mainloop()

if __name__=="__main__": main()
