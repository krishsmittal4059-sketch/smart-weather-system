#!/usr/bin/env python3
"""SMART WEATHER SYSTEM - Raspberry Pi 1 friendly Tkinter dashboard."""
import math
import sys
import tkinter as tk
from collections import deque
from datetime import datetime

from bme280_sensor import BME280Sensor

UPDATE_MS = 2000
MAX_POINTS = 90
SMOOTH_LINES = False
REQUIRED_KEYS = ("temperature", "humidity", "pressure", "altitude")
FONT = "Helvetica"
APP_BG="#070B10"; HEADER_BG="#0D141B"; PANEL="#101820"; PANEL_2="#141F29"
NAV_ACTIVE="#1E2B35"; BORDER="#263541"; GRID="#1D2932"; TEXT="#F3F7FA"
MUTED="#81909D"; DISABLED="#697783"; CYAN="#55D9FF"; GREEN="#49E58A"
YELLOW="#FFD34E"; RED="#FF6675"; PURPLE="#A98CFF"

STATUS={
("TEST",True):(("● SYSTEM ONLINE",GREEN),("SIMULATION • HARDWARE NOT REQUIRED",YELLOW),("SIMULATED SENSOR",YELLOW),"Test generator • safe for exhibition demo"),
("TEST",False):(("● SIMULATOR ERROR",RED),("SIMULATION • GENERATOR FAILED",RED),("SIMULATOR ERROR",RED),"The test generator returned no valid data"),
("LIVE",True):(("● BME280 ONLINE",GREEN),("LIVE • BME280 CONNECTED",GREEN),("BME280 ONLINE",GREEN),"I²C • automatic address scan 0x76 / 0x77"),
("LIVE",False):(("● SENSOR OFFLINE",RED),("LIVE • BME280 NOT CONNECTED",RED),("BME280 OFFLINE",RED),"Check I²C wiring and address 0x76 / 0x77")}

def clamp(v,lo,hi): return max(lo,min(hi,v))
def dew_point(t,h):
    h=clamp(h,.1,100); a,b=17.62,243.12
    g=math.log(h/100)+a*t/(b+t); return b*g/(a-g)
def span(s): return f"{s/60:g} min" if s>=120 else f"{s:g} s"

def label(parent,text="",fg=TEXT,size=10,bg=PANEL,bold=True,**kw):
    return tk.Label(parent,text=text,bg=bg,fg=fg,font=(FONT,size,"bold" if bold else "normal"),**kw)
def panel(parent): return tk.Frame(parent,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
def button(parent,text,command,bg=PANEL_2,fg=TEXT,active_bg="#2A3944",active_fg=None,padx=14,pady=6):
    return tk.Button(parent,text=text,command=command,bg=bg,fg=fg,activebackground=active_bg,activeforeground=active_fg or fg,font=(FONT,9,"bold"),bd=0,padx=padx,pady=pady,cursor="hand2")

class Gauge(tk.Canvas):
    def __init__(self,parent,label_text,unit,minimum,maximum,accent,warn=None,danger=None):
        super().__init__(parent,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        self.label=label_text; self.unit=unit; self.minimum=minimum; self.maximum=maximum; self.accent=accent; self.warn=warn; self.danger=danger; self.value=None; self.arc=None
        self.bind("<Configure>",self.layout)
    def layout(self,event=None):
        w=max(180,self.winfo_width()); h=max(120,self.winfo_height()); self.cx=w/2; self.cy=h*.55; self.r=min(w*.34,h*.34); box=(self.cx-self.r,self.cy-self.r,self.cx+self.r,self.cy+self.r)
        self.delete("all"); self.create_arc(*box,start=135,extent=-270,style="arc",outline=BORDER,width=12)
        self.arc=self.create_arc(*box,start=135,extent=0,style="arc",outline=self.accent,width=12); self.needle=self.create_line(self.cx,self.cy,self.cx,self.cy,fill=TEXT,width=3)
        self.create_oval(self.cx-5,self.cy-5,self.cx+5,self.cy+5,fill=TEXT,outline=""); self.readout=self.create_text(self.cx,self.cy+28,fill=TEXT,font=(FONT,19,"bold")); self.create_text(self.cx,18,text=self.label,fill=MUTED,font=(FONT,10,"bold")); self.set_value(self.value)
    def set_value(self,value):
        self.value=value
        if self.arc is None:return
        if value is None:
            self.itemconfigure(self.arc,extent=0); self.itemconfigure(self.needle,state="hidden"); self.itemconfigure(self.readout,text=f"-- {self.unit}"); return
        ratio=clamp((value-self.minimum)/float(self.maximum-self.minimum),0,1); angle=math.radians(135-270*ratio); x=self.cx+self.r*.76*math.cos(angle); y=self.cy-self.r*.76*math.sin(angle)
        color=RED if self.danger is not None and value>=self.danger else YELLOW if self.warn is not None and value>=self.warn else self.accent
        self.itemconfigure(self.arc,extent=-270*ratio,outline=color); self.coords(self.needle,self.cx,self.cy,x,y); self.itemconfigure(self.needle,state="normal"); self.itemconfigure(self.readout,text=f"{value:.1f} {self.unit}")

class LineChart(tk.Canvas):
    L,R,T,B=16,16,42,24
    def __init__(self,parent,title,unit,accent):
        super().__init__(parent,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); self.title=title; self.unit=unit; self.accent=accent; self.values=(); self.line=None; self.bind("<Configure>",self.layout)
    def layout(self,event=None):
        self.w=max(250,self.winfo_width()); self.h=max(150,self.winfo_height()); gh=self.h-self.T-self.B; self.delete("all")
        for f in (.25,.5,.75): self.create_line(self.L,self.T+gh*f,self.w-self.R,self.T+gh*f,fill=GRID)
        self.create_text(14,12,anchor="nw",text=self.title,fill=TEXT,font=(FONT,12,"bold")); self.create_text(self.L,self.h-5,anchor="sw",text=f"-{span(MAX_POINTS*UPDATE_MS/1000)}",fill=MUTED,font=(FONT,9)); self.create_text(self.w-self.R,self.h-5,anchor="se",text="now",fill=MUTED,font=(FONT,9))
        self.empty=self.create_text(self.w/2,self.h/2,text="Waiting for measurements...",fill=MUTED,font=(FONT,11)); self.range=self.create_text(self.w-self.R,14,anchor="ne",fill=MUTED,font=(FONT,9)); self.line=self.create_line(0,0,0,0,fill=self.accent,width=3,smooth=SMOOTH_LINES,state="hidden"); self.dot=self.create_oval(0,0,0,0,fill=self.accent,outline="",state="hidden"); self.set_data(self.values)
    def set_data(self,values):
        self.values=values
        if self.line is None:return
        vals=list(values)
        if not vals:
            self.itemconfigure(self.empty,state="normal"); self.itemconfigure(self.line,state="hidden"); self.itemconfigure(self.dot,state="hidden"); self.itemconfigure(self.range,state="hidden"); return
        lo,hi=min(vals),max(vals); pad=max(abs(hi)*.01,1) if hi==lo else (hi-lo)*.08; floor,ceil=lo-pad,hi+pad; gw=self.w-self.L-self.R; gh=self.h-self.T-self.B; step=gw/(MAX_POINTS-1); offset=MAX_POINTS-len(vals); pts=[]
        for i,v in enumerate(vals): pts += [self.L+(offset+i)*step,self.T+(ceil-v)*gh/(ceil-floor)]
        x,y=pts[-2:]; self.coords(self.dot,x-4,y-4,x+4,y+4); self.itemconfigure(self.dot,state="normal"); self.itemconfigure(self.empty,state="hidden"); self.itemconfigure(self.range,state="normal",text=f"min {lo:.1f}   max {hi:.1f} {self.unit}")
        if len(vals)>1:self.coords(self.line,*pts); self.itemconfigure(self.line,state="normal")
        else:self.itemconfigure(self.line,state="hidden")

class WeatherApp:
    def __init__(self,root,fullscreen=True):
        self.root=root; self.mode="TEST"; self.page="DASHBOARD"; self.sensor=BME280Sensor(test_mode=True); self.history={k:deque(maxlen=MAX_POINTS) for k in ("temperature","humidity","pressure")}; self.latest=None; self.t_min=None; self.t_max=None; self.sample_job=None; self.clock_job=None; self.fullscreen=fullscreen
        self.build_window(); self.build_header(); self.build_nav(); self.build_footer(); self.build_pages(); self.show_page("DASHBOARD"); self.set_mode("TEST"); self.tick_clock()
    def build_window(self):
        self.root.title("Smart Weather System — Advanced Station Console"); self.root.configure(bg=APP_BG); self.root.attributes("-fullscreen",self.fullscreen); self.root.minsize(800,480); self.root.bind("<Escape>",lambda e:self.set_fullscreen(False)); self.root.bind("<F11>",lambda e:self.set_fullscreen(not self.fullscreen)); self.root.bind("<Control-q>",lambda e:self.close()); self.root.protocol("WM_DELETE_WINDOW",self.close)
    def set_fullscreen(self,v): self.fullscreen=v; self.root.attributes("-fullscreen",v)
    def close(self):
        for job in (self.sample_job,self.clock_job):
            if job:
                try:self.root.after_cancel(job)
                except tk.TclError:pass
        close=getattr(self.sensor,"close",None)
        if callable(close):
            try:close()
            except Exception:pass
        self.root.destroy()
    def build_header(self):
        h=tk.Frame(self.root,bg=HEADER_BG,height=70); h.pack(fill="x",padx=6,pady=(6,2)); h.pack_propagate(False); b=tk.Frame(h,bg=HEADER_BG); b.pack(side="left",padx=18); label(b,"◈",fg=CYAN,size=26,bg=HEADER_BG).pack(side="left",padx=(0,10)); label(b,"SMART WEATHER",size=20,bg=HEADER_BG).pack(anchor="w"); label(b,"ADVANCED STATION CONSOLE",fg=MUTED,size=8,bg=HEADER_BG).pack(anchor="w"); self.mode_label=label(h,"TEST",fg=YELLOW,size=13,bg=HEADER_BG); self.mode_label.pack(side="left",padx=22); self.connection=label(h,"",size=11,bg=HEADER_BG); self.connection.pack(side="left"); self.clock=label(h,"",size=12,bg=HEADER_BG); self.clock.pack(side="right",padx=18)
    def build_nav(self):
        n=tk.Frame(self.root,bg=APP_BG); n.pack(fill="x",padx=12,pady=3); self.nav={}
        for p in ("DASHBOARD","ANALYTICS"):
            x=button(n,p,lambda p=p:self.show_page(p),fg=MUTED,active_fg=CYAN,padx=18); x.pack(side="left",padx=3); self.nav[p]=x
        self.mode_button=button(n,"SWITCH TO LIVE",self.toggle_mode,bg="#075D31",active_bg="#078A48"); self.mode_button.pack(side="right",padx=3); self.status=label(self.root,"",size=9,bg=APP_BG); self.status.pack(pady=1)
    def build_footer(self):
        f=tk.Frame(self.root,bg=HEADER_BG,height=42); f.pack(side="bottom",fill="x",padx=6,pady=(2,6)); f.pack_propagate(False); button(f,"RESET HISTORY",self.clear_history,padx=12,pady=5).pack(side="left",padx=(10,5),pady=5); label(f,"ESC  EXIT FULLSCREEN   •   F11  TOGGLE FULLSCREEN   •   CTRL+Q  QUIT",fg=MUTED,size=8,bg=HEADER_BG).pack(side="left",padx=12); label(f,f"REFRESH  {UPDATE_MS/1000:g}s",fg=MUTED,size=8,bg=HEADER_BG).pack(side="right",padx=15)
    def build_pages(self):
        s=tk.Frame(self.root,bg=APP_BG); s.pack(fill="both",expand=True,padx=8,pady=2); self.dashboard=tk.Frame(s,bg=APP_BG); self.analytics=tk.Frame(s,bg=APP_BG); self.dashboard.place(relx=0,rely=0,relwidth=1,relheight=1); self.analytics.place(relx=0,rely=0,relwidth=1,relheight=1); self.build_dashboard(); self.build_analytics()
    def card(self,p,c,title,value):
        x=panel(p); x.grid(row=0,column=c,sticky="nsew",padx=5,pady=5); label(x,title,fg=MUTED,size=11).pack(anchor="w",padx=12,pady=(8,0)); v=label(x,value,size=23); v.pack(anchor="w",padx=12,pady=(1,8)); return v
    def build_dashboard(self):
        p=self.dashboard
        for c in range(3):p.grid_columnconfigure(c,weight=1)
        p.grid_rowconfigure(1,weight=1); p.grid_rowconfigure(2,weight=1)
        self.temp_value=self.card(p,0,"TEMPERATURE","-- °C"); self.humidity_value=self.card(p,1,"HUMIDITY","-- %"); self.pressure_value=self.card(p,2,"PRESSURE","---- hPa")
        self.temp_gauge=Gauge(p,"TEMPERATURE","°C",0,50,CYAN,35,42); self.humidity_gauge=Gauge(p,"HUMIDITY","%",0,100,GREEN); self.pressure_gauge=Gauge(p,"PRESSURE","hPa",950,1050,PURPLE)
        for c,g in enumerate((self.temp_gauge,self.humidity_gauge,self.pressure_gauge)):g.grid(row=1,column=c,sticky="nsew",padx=5,pady=5)
        self.temp_chart=LineChart(p,"TEMPERATURE TREND","°C",CYAN); self.pressure_chart=LineChart(p,"PRESSURE TREND","hPa",PURPLE); self.temp_chart.grid(row=2,column=0,sticky="nsew",padx=5,pady=5); self.pressure_chart.grid(row=2,column=1,sticky="nsew",padx=5,pady=5)
        info=panel(p); info.grid(row=2,column=2,sticky="nsew",padx=5,pady=5); label(info,"STATION HEALTH",fg=MUTED,size=11).pack(anchor="w",padx=12,pady=(10,8)); self.sensor_state=label(info,"",size=14); self.sensor_state.pack(anchor="w",padx=12); self.sensor_detail=label(info,"",fg=MUTED,size=9,bold=False,wraplength=260,justify="left"); self.sensor_detail.pack(anchor="w",padx=12,pady=(3,12)); label(info,"TEMPERATURE RANGE",fg=MUTED,size=9).pack(anchor="w",padx=12); self.range=label(info,"-- / -- °C",size=16); self.range.pack(anchor="w",padx=12,pady=(1,10)); label(info,"ALTITUDE",fg=MUTED,size=9).pack(anchor="w",padx=12); self.altitude=label(info,"-- m",size=16); self.altitude.pack(anchor="w",padx=12,pady=(1,10)); label(info,"DEW POINT",fg=MUTED,size=9).pack(anchor="w",padx=12); self.dew=label(info,"-- °C",size=16); self.dew.pack(anchor="w",padx=12,pady=(1,10)); label(info,"RAIN SENSOR",fg=DISABLED,size=9).pack(anchor="w",padx=12); label(info,"NOT CONNECTED",fg=DISABLED,size=12).pack(anchor="w",padx=12,pady=(1,10)); self.last=label(info,"Waiting for measurement...",fg=MUTED,size=9,bold=False); self.last.pack(anchor="w",padx=12,pady=4)
    def build_analytics(self):
        p=self.analytics
        for c in range(2):p.grid_columnconfigure(c,weight=1)
        for r in range(3):p.grid_rowconfigure(r,weight=1)
        self.analytic_temp=LineChart(p,"TEMPERATURE HISTORY","°C",CYAN); self.analytic_pressure=LineChart(p,"PRESSURE HISTORY","hPa",PURPLE); self.analytic_humidity=LineChart(p,"HUMIDITY HISTORY","%",GREEN); self.analytic_temp.grid(row=0,column=0,sticky="nsew",padx=5,pady=5); self.analytic_pressure.grid(row=0,column=1,sticky="nsew",padx=5,pady=5); self.analytic_humidity.grid(row=1,column=0,columnspan=2,sticky="nsew",padx=5,pady=5); self.stats=label(p,"Waiting for measurements...",size=11,bg=PANEL_2); self.stats.grid(row=2,column=0,columnspan=2,sticky="ew",padx=18,pady=8)
    def show_page(self,p):
        self.page=p; (self.dashboard if p=="DASHBOARD" else self.analytics).tkraise()
        for n,b in self.nav.items():b.config(bg=NAV_ACTIVE if n==p else PANEL_2,fg=CYAN if n==p else MUTED)
        self.redraw()
    def toggle_mode(self):self.set_mode("LIVE" if self.mode=="TEST" else "TEST")
    def set_mode(self,m):
        self.mode=m; self.clear_history(False)
        self.mode_label.config(text=m,fg=YELLOW if m=="TEST" else GREEN); self.mode_button.config(text="SWITCH TO LIVE" if m=="TEST" else "SWITCH TO TEST",bg="#075D31" if m=="TEST" else "#5C4D00",activebackground="#078A48" if m=="TEST" else "#806E00"); self.sample()
    def read(self):
        try:self.sensor.test_mode=self.mode=="TEST"; d=self.sensor.read()
        except Exception:return None
        if not isinstance(d,dict) or (self.mode=="LIVE" and not d.get("sensor_ok",False)):return None
        try:r={k:float(d[k]) for k in REQUIRED_KEYS}
        except (KeyError,TypeError,ValueError):return None
        return None if any(math.isnan(v) or math.isinf(v) for v in r.values()) else r
    def sample(self):
        self.sample_job=None; d=self.read()
        if d is None:self.latest=None; self.offline()
        else:self.latest=d; self.record(d); self.online(d)
        self.redraw(); self.sample_job=self.root.after(UPDATE_MS,self.sample)
    def record(self,d):
        t=d["temperature"]; self.t_min=t if self.t_min is None else min(self.t_min,t); self.t_max=t if self.t_max is None else max(self.t_max,t); [self.history[k].append(d[k]) for k in self.history]
    def online(self,d):
        self.temp_value.config(text=f"{d['temperature']:.1f} °C"); self.humidity_value.config(text=f"{d['humidity']:.1f} %"); self.pressure_value.config(text=f"{d['pressure']:.1f} hPa"); self.altitude.config(text=f"{d['altitude']:.1f} m"); self.dew.config(text=f"{dew_point(d['temperature'],d['humidity']):.1f} °C"); self.range.config(text=f"{self.t_min:.1f} / {self.t_max:.1f} °C"); s=STATUS[(self.mode,True)]; self.set_status(s); self.last.config(text=f"Last sample  {datetime.now().strftime('%H:%M:%S')}")
    def offline(self):
        self.temp_value.config(text="-- °C"); self.humidity_value.config(text="-- %"); self.pressure_value.config(text="---- hPa"); self.altitude.config(text="-- m"); self.dew.config(text="-- °C"); self.range.config(text="-- / -- °C"); self.last.config(text="No valid reading"); self.set_status(STATUS[(self.mode,False)])
    def set_status(self,s):
        (a,ac),(b,bc),(c,cc),detail=s; self.connection.config(text=a,fg=ac); self.status.config(text=b,fg=bc); self.sensor_state.config(text=c,fg=cc); self.sensor_detail.config(text=detail)
    def redraw(self):
        if self.page=="DASHBOARD":
            d=self.latest or {}; self.temp_gauge.set_value(d.get("temperature")); self.humidity_gauge.set_value(d.get("humidity")); self.pressure_gauge.set_value(d.get("pressure")); self.temp_chart.set_data(self.history["temperature"]); self.pressure_chart.set_data(self.history["pressure"])
        else:
            self.analytic_temp.set_data(self.history["temperature"]); self.analytic_pressure.set_data(self.history["pressure"]); self.analytic_humidity.set_data(self.history["humidity"]); v=list(self.history["temperature"]); self.stats.config(text="Waiting for measurements..." if not v else f"SAMPLES  {len(v)}    AVG TEMP  {sum(v)/len(v):.1f} °C    MIN  {min(v):.1f} °C    MAX  {max(v):.1f} °C")
    def clear_history(self,redraw=True):
        for v in self.history.values():v.clear()
        self.latest=None; self.t_min=None; self.t_max=None
        if hasattr(self,"range"):self.range.config(text="-- / -- °C")
        if redraw:self.redraw()
    def tick_clock(self):self.clock.config(text=datetime.now().strftime("%d %b %Y   %H:%M:%S")); self.clock_job=self.root.after(1000,self.tick_clock)

def main():
    root=tk.Tk(); WeatherApp(root,fullscreen="--windowed" not in sys.argv); root.mainloop()
if __name__=="__main__":main()
