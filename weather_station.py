import tkinter as tk
import math
import sys
from collections import deque
from datetime import datetime

from bme280_sensor import BME280Sensor

APP_BG="#070B10"; PANEL="#101820"; PANEL_2="#141F29"; BORDER="#263541"
TEXT="#F3F7FA"; MUTED="#81909D"; CYAN="#55D9FF"; GREEN="#49E58A"
YELLOW="#FFD34E"; RED="#FF6675"; PURPLE="#A98CFF"
UPDATE_MS=2000; MAX_POINTS=90; MODE="TEST"
temperature_history=deque(maxlen=MAX_POINTS); pressure_history=deque(maxlen=MAX_POINTS); humidity_history=deque(maxlen=MAX_POINTS)
temperature_min=None; temperature_max=None; update_job=None
sensor=BME280Sensor(test_mode=True)

def clamp(v,lo,hi): return max(lo,min(hi,v))
def make_panel(p): return tk.Frame(p,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
def make_title(p,t,size=11): return tk.Label(p,text=t,bg=PANEL,fg=MUTED,font=("Arial",size,"bold"))
def dew_point(t,h):
    h=clamp(h,.1,100); a,b=17.62,243.12; g=math.log(h/100)+a*t/(b+t); return b*g/(a-g)

def get_data():
    sensor.test_mode=MODE=="TEST"; return sensor.read()

def draw_gauge(c,v,mi,ma,label,unit,accent):
    c.delete("all"); w=max(180,c.winfo_width()); h=max(120,c.winfo_height()); cx=w/2; cy=h*.55; r=min(w*.34,h*.34)
    c.create_arc(cx-r,cy-r,cx+r,cy+r,start=135,extent=-270,style="arc",outline=BORDER,width=12)
    if v is None: text=f"-- {unit}"
    else:
        q=clamp((v-mi)/float(ma-mi),0,1); c.create_arc(cx-r,cy-r,cx+r,cy+r,start=135,extent=-270*q,style="arc",outline=accent,width=12)
        a=math.radians(135-270*q); x=cx+r*.76*math.cos(a); y=cy-r*.76*math.sin(a); c.create_line(cx,cy,x,y,fill=TEXT,width=3); c.create_oval(cx-5,cy-5,cx+5,cy+5,fill=TEXT,outline=""); text=f"{v:.1f} {unit}"
    c.create_text(cx,cy+28,text=text,fill=TEXT,font=("Arial",19,"bold")); c.create_text(cx,18,text=label,fill=MUTED,font=("Arial",10,"bold"))

def draw_graph(c,vals,title,unit,accent):
    c.delete("all"); w=max(250,c.winfo_width()); h=max(150,c.winfo_height()); c.create_text(14,12,anchor="nw",text=title,fill=TEXT,font=("Arial",12,"bold"))
    if not vals: c.create_text(w/2,h/2,text="Waiting for measurements...",fill=MUTED,font=("Arial",11)); return
    v=list(vals); lo,hi=min(v),max(v)
    if lo==hi: pad=max(abs(hi)*.01,1.0); lo-=pad; hi+=pad
    left,right,top,bottom=16,16,42,24; gw=w-left-right; gh=h-top-bottom
    for f in (.25,.5,.75): c.create_line(left,top+gh*f,w-right,top+gh*f,fill="#1D2932")
    pts=[]
    for i,xv in enumerate(v):
        x=left+(i*gw/(len(v)-1) if len(v)>1 else gw/2); y=top+(hi-xv)*gh/(hi-lo); pts.extend((x,y))
    if len(pts)>=4: c.create_line(*pts,fill=accent,width=3)
    x,y=pts[-2:]; c.create_oval(x-4,y-4,x+4,y+4,fill=accent,outline="")
    c.create_text(w-right,top,anchor="ne",text=f"max {max(v):.1f} {unit}",fill=MUTED,font=("Arial",9))
    c.create_text(w-right,h-5,anchor="se",text=f"min {min(v):.1f} {unit}",fill=MUTED,font=("Arial",9))

def update_analytics():
    draw_graph(analytics_temp,temperature_history,"TEMPERATURE HISTORY","°C",CYAN); draw_graph(analytics_pressure,pressure_history,"PRESSURE HISTORY","hPa",PURPLE); draw_graph(analytics_humidity,humidity_history,"HUMIDITY HISTORY","%",GREEN)
    if temperature_history:
        a=sum(temperature_history)/len(temperature_history); analytics_stats.config(text=f"SAMPLES  {len(temperature_history)}    AVG TEMP  {a:.1f} °C    MIN  {min(temperature_history):.1f} °C    MAX  {max(temperature_history):.1f} °C")
    else: analytics_stats.config(text="Waiting for measurements...")

def redraw():
    if page=="DASHBOARD":
        d=latest or {}; draw_gauge(temp_gauge,d.get("temperature"),0,50,"TEMPERATURE","°C",CYAN); draw_gauge(humidity_gauge,d.get("humidity"),0,100,"HUMIDITY","%",GREEN); draw_gauge(pressure_gauge,d.get("pressure"),950,1050,"PRESSURE","hPa",PURPLE); draw_graph(temp_chart,temperature_history,"TEMPERATURE TREND","°C",CYAN); draw_graph(pressure_chart,pressure_history,"PRESSURE TREND","hPa",PURPLE)
    else: update_analytics()

def clear_history():
    global temperature_min,temperature_max
    temperature_history.clear(); pressure_history.clear(); humidity_history.clear(); temperature_min=temperature_max=None; redraw()

def show_page(p):
    global page
    page=p; (dashboard_frame if p=="DASHBOARD" else analytics_frame).tkraise()
    for n,b in nav_buttons.items(): b.config(bg="#1E2B35" if n==p else PANEL_2,fg=CYAN if n==p else MUTED)
    redraw()

def toggle_mode(): set_mode("LIVE" if MODE=="TEST" else "TEST")
def set_mode(m):
    global MODE,update_job,latest
    MODE="TEST" if m=="TEST" else "LIVE"; latest=None; clear_history()
    if update_job:
        try: root.after_cancel(update_job)
        except Exception: pass
    mode_label.config(text=MODE,fg=YELLOW if MODE=="TEST" else GREEN); mode_button.config(text="SWITCH TO LIVE" if MODE=="TEST" else "SWITCH TO TEST",bg="#075D31" if MODE=="TEST" else "#5C4D00",activebackground="#078A48" if MODE=="TEST" else "#806E00")
    update_display()

def update_display():
    global update_job,latest,temperature_min,temperature_max
    try:
        d=get_data(); ok=isinstance(d,dict) and all(k in d for k in ("temperature","humidity","pressure","altitude")) and (MODE=="TEST" or d.get("sensor_ok",False))
        if not ok:
            latest=None; temp_value.config(text="-- °C"); humidity_value.config(text="-- %"); pressure_value.config(text="---- hPa"); altitude_value.config(text="-- m"); connection_label.config(text="● SENSOR OFFLINE",fg=RED); status_label.config(text="LIVE • BME280 NOT CONNECTED",fg=RED); sensor_state.config(text="BME280 OFFLINE",fg=RED); sensor_detail.config(text="Check I²C wiring and address 0x76 / 0x77"); last_reading.config(text="No valid reading")
        else:
            t,h,p,a=map(float,(d["temperature"],d["humidity"],d["pressure"],d["altitude"])); latest={"temperature":t,"humidity":h,"pressure":p,"altitude":a}; temperature_history.append(t); humidity_history.append(h); pressure_history.append(p); temperature_min=t if temperature_min is None else min(temperature_min,t); temperature_max=t if temperature_max is None else max(temperature_max,t)
            temp_value.config(text=f"{t:.1f} °C"); humidity_value.config(text=f"{h:.1f} %"); pressure_value.config(text=f"{p:.1f} hPa"); altitude_value.config(text=f"{a:.1f} m"); temp_range_value.config(text=f"{temperature_min:.1f} / {temperature_max:.1f} °C")
            if MODE=="TEST": connection_label.config(text="● SYSTEM ONLINE",fg=GREEN); status_label.config(text="SIMULATION • HARDWARE NOT REQUIRED",fg=YELLOW); sensor_state.config(text="SIMULATED SENSOR",fg=YELLOW); sensor_detail.config(text="Test generator • safe for exhibition demo")
            else: connection_label.config(text="● BME280 ONLINE",fg=GREEN); status_label.config(text="LIVE • BME280 CONNECTED",fg=GREEN); sensor_state.config(text="BME280 ONLINE",fg=GREEN); sensor_detail.config(text="I²C • automatic address scan 0x76 / 0x77")
            last_reading.config(text=f"Last sample {datetime.now().strftime('%H:%M:%S')}"); redraw()
    except Exception as e: print("Update error:",e)
    update_job=root.after(UPDATE_MS,update_display)

def tick_clock(): clock_label.config(text=datetime.now().strftime("%d %b %Y   %H:%M:%S")); root.after(1000,tick_clock)
def close_app(e=None):
    global update_job
    if update_job:
        try: root.after_cancel(update_job)
        except Exception: pass
    root.destroy()

root=tk.Tk(); root.title("Smart Weather System — Advanced Station Console"); root.configure(bg=APP_BG); root.attributes("-fullscreen","--windowed" not in sys.argv); root.minsize(900,600); root.bind("<Escape>",lambda e:root.attributes("-fullscreen",False)); root.bind("<F11>",lambda e:root.attributes("-fullscreen",not bool(root.attributes("-fullscreen")))); root.bind("<Control-q>",close_app); root.protocol("WM_DELETE_WINDOW",close_app)
header=tk.Frame(root,bg="#0D141B",height=70); header.pack(fill="x",padx=6,pady=(6,2)); header.pack_propagate(False)
brand=tk.Frame(header,bg="#0D141B"); brand.pack(side="left",padx=18); tk.Label(brand,text="◈",bg="#0D141B",fg=CYAN,font=("Arial",26,"bold")).pack(side="left",padx=(0,10)); tk.Label(brand,text="SMART WEATHER",bg="#0D141B",fg=TEXT,font=("Arial",20,"bold")).pack(anchor="w"); tk.Label(brand,text="ADVANCED STATION CONSOLE",bg="#0D141B",fg=MUTED,font=("Arial",8,"bold")).pack(anchor="w")
mode_label=tk.Label(header,text="TEST",bg="#0D141B",fg=YELLOW,font=("Arial",13,"bold")); mode_label.pack(side="left",padx=22); connection_label=tk.Label(header,text="● SYSTEM ONLINE",bg="#0D141B",fg=GREEN,font=("Arial",11,"bold")); connection_label.pack(side="left"); clock_label=tk.Label(header,text="",bg="#0D141B",fg=TEXT,font=("Arial",12,"bold")); clock_label.pack(side="right",padx=18)
nav=tk.Frame(root,bg=APP_BG); nav.pack(fill="x",padx=12,pady=3); nav_buttons={}
for p in ("DASHBOARD","ANALYTICS"):
    b=tk.Button(nav,text=p,command=lambda x=p:show_page(x),bg=PANEL_2,fg=MUTED,activebackground="#24343F",activeforeground=CYAN,font=("Arial",9,"bold"),bd=0,padx=18,pady=6,cursor="hand2"); b.pack(side="left",padx=3); nav_buttons[p]=b
mode_button=tk.Button(nav,text="SWITCH TO LIVE",command=toggle_mode,bg="#075D31",fg=TEXT,activebackground="#078A48",font=("Arial",9,"bold"),bd=0,padx=14,pady=6,cursor="hand2"); mode_button.pack(side="right",padx=3)
status_label=tk.Label(root,text="SIMULATION • HARDWARE NOT REQUIRED",bg=APP_BG,fg=YELLOW,font=("Arial",9,"bold")); status_label.pack(pady=1)
stack=tk.Frame(root,bg=APP_BG); stack.pack(fill="both",expand=True,padx=8,pady=2); dashboard_frame=tk.Frame(stack,bg=APP_BG); analytics_frame=tk.Frame(stack,bg=APP_BG)
for f in (dashboard_frame,analytics_frame): f.place(relx=0,rely=0,relwidth=1,relheight=1)
for c in range(3): dashboard_frame.grid_columnconfigure(c,weight=1)
dashboard_frame.grid_rowconfigure(0,weight=0); dashboard_frame.grid_rowconfigure(1,weight=1); dashboard_frame.grid_rowconfigure(2,weight=1)
def value_card(parent,col,title,value):
    card=make_panel(parent); card.grid(row=0,column=col,sticky="nsew",padx=5,pady=5); make_title(card,title).pack(anchor="w",padx=12,pady=(8,0)); v=tk.Label(card,text=value,bg=PANEL,fg=TEXT,font=("Arial",23,"bold")); v.pack(anchor="w",padx=12,pady=(1,8)); return v
temp_value=value_card(dashboard_frame,0,"TEMPERATURE","-- °C"); humidity_value=value_card(dashboard_frame,1,"HUMIDITY","-- %"); pressure_value=value_card(dashboard_frame,2,"PRESSURE","---- hPa")
temp_gauge=tk.Canvas(dashboard_frame,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); humidity_gauge=tk.Canvas(dashboard_frame,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); pressure_gauge=tk.Canvas(dashboard_frame,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
for c,v in enumerate((temp_gauge,humidity_gauge,pressure_gauge)): v.grid(row=1,column=c,sticky="nsew",padx=5,pady=5)
temp_chart=tk.Canvas(dashboard_frame,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); pressure_chart=tk.Canvas(dashboard_frame,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); temp_chart.grid(row=2,column=0,sticky="nsew",padx=5,pady=5); pressure_chart.grid(row=2,column=1,sticky="nsew",padx=5,pady=5)
info=make_panel(dashboard_frame); info.grid(row=2,column=2,sticky="nsew",padx=5,pady=5); make_title(info,"STATION HEALTH").pack(anchor="w",padx=12,pady=(10,8)); sensor_state=tk.Label(info,text="SIMULATED SENSOR",bg=PANEL,fg=YELLOW,font=("Arial",14,"bold")); sensor_state.pack(anchor="w",padx=12); sensor_detail=tk.Label(info,text="Test generator • safe for exhibition demo",bg=PANEL,fg=MUTED,justify="left",font=("Arial",9),wraplength=260); sensor_detail.pack(anchor="w",padx=12,pady=(3,12)); tk.Label(info,text="TEMPERATURE RANGE",bg=PANEL,fg=MUTED,font=("Arial",9,"bold")).pack(anchor="w",padx=12); temp_range_value=tk.Label(info,text="-- / -- °C",bg=PANEL,fg=TEXT,font=("Arial",16,"bold")); temp_range_value.pack(anchor="w",padx=12,pady=(1,10)); tk.Label(info,text="ALTITUDE",bg=PANEL,fg=MUTED,font=("Arial",9,"bold")).pack(anchor="w",padx=12); altitude_value=tk.Label(info,text="-- m",bg=PANEL,fg=TEXT,font=("Arial",16,"bold")); altitude_value.pack(anchor="w",padx=12,pady=(1,10)); tk.Label(info,text="RAIN SENSOR",bg=PANEL,fg=MUTED,font=("Arial",9,"bold")).pack(anchor="w",padx=12); tk.Label(info,text="NOT CONNECTED",bg=PANEL,fg="#697783",font=("Arial",12,"bold")).pack(anchor="w",padx=12,pady=(1,10)); last_reading=tk.Label(info,text="Waiting for measurement...",bg=PANEL,fg=MUTED,font=("Arial",9)); last_reading.pack(anchor="w",padx=12,pady=(4,10))
for c in range(2): analytics_frame.grid_columnconfigure(c,weight=1)
for r in range(3): analytics_frame.grid_rowconfigure(r,weight=1)
analytics_temp=tk.Canvas(analytics_frame,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); analytics_pressure=tk.Canvas(analytics_frame,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); analytics_humidity=tk.Canvas(analytics_frame,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
analytics_temp.grid(row=0,column=0,sticky="nsew",padx=5,pady=5); analytics_pressure.grid(row=0,column=1,sticky="nsew",padx=5,pady=5); analytics_humidity.grid(row=1,column=0,columnspan=2,sticky="nsew",padx=5,pady=5)
analytics_stats=tk.Label(analytics_frame,text="Waiting for measurements...",bg=PANEL_2,fg=TEXT,font=("Arial",11,"bold")); analytics_stats.grid(row=2,column=0,columnspan=2,sticky="ew",padx=18,pady=8)
footer=tk.Frame(root,bg="#0D141B",height=42); footer.pack(fill="x",padx=6,pady=(2,6)); footer.pack_propagate(False)
tk.Button(footer,text="RESET HISTORY",command=clear_history,bg=PANEL_2,fg=TEXT,activebackground="#2A3944",font=("Arial",9,"bold"),bd=0,padx=12,pady=5,cursor="hand2").pack(side="left",padx=(10,5),pady=5)
tk.Label(footer,text="ESC  EXIT FULLSCREEN   •   F11  TOGGLE FULLSCREEN   •   CTRL+Q  QUIT",bg="#0D141B",fg=MUTED,font=("Arial",8,"bold")).pack(side="left",padx=12)
update_counter=tk.Label(footer,text="REFRESH  2s",bg="#0D141B",fg=MUTED,font=("Arial",8,"bold")); update_counter.pack(side="right",padx=15)
latest=None; page="DASHBOARD"
show_page("DASHBOARD"); set_mode("TEST"); tick_clock(); root.mainloop()
