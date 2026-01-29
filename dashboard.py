import tkinter as tk
from tkinter import messagebox
import psutil
import sqlite3
import csv
import time
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ================= DATABASE =================
conn = sqlite3.connect("system_health.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS system_health (
    timestamp TEXT,
    cpu REAL,
    memory REAL,
    disk REAL,
    battery REAL,
    risk TEXT
)
""")
conn.commit()

# ================= WINDOW =================
root = tk.Tk()
root.title("System Health Monitoring Dashboard")
root.geometry("1200x650")
root.resizable(False, False)

# ================= LEFT PANEL =================
left = tk.Frame(root, bg="#2c3e50", width=260)
left.pack(side="left", fill="y")

tk.Label(
    left, text="SYSTEM HEALTH",
    fg="white", bg="#2c3e50",
    font=("Arial", 18, "bold")
).pack(pady=20)

lbl_cpu = tk.Label(left, fg="white", bg="#2c3e50", font=("Arial", 13))
lbl_mem = tk.Label(left, fg="white", bg="#2c3e50", font=("Arial", 13))
lbl_disk = tk.Label(left, fg="white", bg="#2c3e50", font=("Arial", 13))
lbl_bat = tk.Label(left, fg="white", bg="#2c3e50", font=("Arial", 13))
lbl_risk = tk.Label(left, font=("Arial", 14, "bold"))

for w in (lbl_cpu, lbl_mem, lbl_disk, lbl_bat, lbl_risk):
    w.pack(pady=6)

# ================= RIGHT PANEL =================
right = tk.Frame(root, bg="white")
right.pack(side="right", expand=True, fill="both")

content = tk.Frame(right, bg="white")
content.pack(expand=True, fill="both")

# ================= HELPERS =================
def clear_content():
    for w in content.winfo_children():
        w.destroy()

def detect_risk(cpu, mem, disk):
    high = sum([cpu >= 85, mem >= 85, disk >= 90])
    if high >= 2:
        return "CRITICAL", "red"
    elif cpu >= 70 or mem >= 75 or disk >= 80:
        return "WARNING", "orange"
    else:
        return "NORMAL", "green"

# ================= LIVE STATUS =================
def show_live_status():
    clear_content()

    tk.Label(
        content,
        text="LIVE SYSTEM STATUS",
        font=("Arial", 16, "bold"),
        bg="white"
    ).pack(pady=15)

    global r_cpu, r_mem, r_disk, r_bat, r_risk

    r_cpu = tk.Label(content, font=("Arial", 14), bg="white")
    r_mem = tk.Label(content, font=("Arial", 14), bg="white")
    r_disk = tk.Label(content, font=("Arial", 14), bg="white")
    r_bat = tk.Label(content, font=("Arial", 14), bg="white")
    r_risk = tk.Label(content, font=("Arial", 15, "bold"), pady=10)

    r_cpu.pack()
    r_mem.pack()
    r_disk.pack()
    r_bat.pack()
    r_risk.pack(pady=15)

# ================= CURRENT BAR GRAPH =================
def show_graphs():
    clear_content()

    cur.execute("""
    SELECT cpu, memory, disk, battery
    FROM system_health
    ORDER BY timestamp DESC
    LIMIT 1
    """)
    row = cur.fetchone()

    if not row:
        tk.Label(content, text="No data yet", bg="white").pack()
        return

    labels = ["CPU", "Memory", "Disk", "Battery"]
    values = list(row)

    fig = plt.Figure(figsize=(7, 4))
    ax = fig.add_subplot(111)
    ax.barh(labels, values)
    ax.set_xlim(0, 100)
    ax.set_title("Current Resource Usage")
    ax.set_xlabel("Usage %")

    for i, v in enumerate(values):
        ax.text(v + 1, i, f"{v}%", va="center")

    canvas = FigureCanvasTkAgg(fig, content)
    canvas.draw()
    canvas.get_tk_widget().pack(expand=True, fill="both")

# ================= LAST 5 MINUTES GRAPH =================
def show_past_5_minutes():
    clear_content()

    tk.Label(
        content,
        text="LAST 5 MINUTES – RESOURCE GRAPH",
        font=("Arial", 16, "bold"),
        bg="white"
    ).pack(pady=10)

    since = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
    SELECT timestamp, cpu, memory, disk
    FROM system_health
    WHERE timestamp >= ?
    ORDER BY timestamp
    """, (since,))
    rows = cur.fetchall()

    if not rows:
        tk.Label(content, text="No data available", bg="white").pack()
        return

    times = [r[0][-8:] for r in rows]
    cpu = [r[1] for r in rows]
    mem = [r[2] for r in rows]
    disk = [r[3] for r in rows]

    fig = plt.Figure(figsize=(8, 4))
    ax = fig.add_subplot(111)
    ax.plot(times, cpu, label="CPU")
    ax.plot(times, mem, label="Memory")
    ax.plot(times, disk, label="Disk")

    ax.set_title("Last 5 Minutes Usage")
    ax.set_ylabel("Usage %")
    ax.legend()
    ax.tick_params(axis='x', rotation=45)

    canvas = FigureCanvasTkAgg(fig, content)
    canvas.draw()
    canvas.get_tk_widget().pack(expand=True, fill="both")

# ================= TODAY USAGE =================
def show_today_usage():
    clear_content()
    uptime = round((time.time() - psutil.boot_time()) / 3600, 2)

    tk.Label(content, text="TODAY SYSTEM USAGE",
             font=("Arial", 16, "bold"), bg="white").pack(pady=20)

    tk.Label(content, text=f"System Uptime : {uptime} hours",
             font=("Arial", 14), bg="white").pack()

# ================= SAVE REPORT =================
def save_report():
    cur.execute("SELECT * FROM system_health")
    rows = cur.fetchall()

    with open("system_health_report.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp","CPU","Memory","Disk","Battery","Risk"])
        writer.writerows(rows)

    messagebox.showinfo("Saved", "Report saved successfully")

# ================= LIVE UPDATE =================
def live_update():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    bat = psutil.sensors_battery()
    battery = bat.percent if bat else 0

    risk, color = detect_risk(cpu, mem, disk)

    lbl_cpu.config(text=f"CPU : {cpu}%")
    lbl_mem.config(text=f"Memory : {mem}%")
    lbl_disk.config(text=f"Disk : {disk}%")
    lbl_bat.config(text=f"Battery : {battery}%")
    lbl_risk.config(text=f"SYSTEM STATUS : {risk}", bg=color, fg="white")

    try:
        r_cpu.config(text=f"CPU Usage       : {cpu}%")
        r_mem.config(text=f"Memory Usage    : {mem}%")
        r_disk.config(text=f"Disk Usage      : {disk}%")
        r_bat.config(text=f"Battery Level   : {battery}%")
        r_risk.config(text=f"SYSTEM STATUS : {risk}", bg=color, fg="white")
    except:
        pass

    cur.execute("""
    INSERT INTO system_health
    VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          cpu, mem, disk, battery, risk))
    conn.commit()

    root.after(3000, live_update)

# ================= BUTTONS =================
btn = {"bg":"#34495e","fg":"white","font":("Arial",12),"width":20,"pady":6}

tk.Button(left, text="Live Status", command=show_live_status, **btn).pack(pady=4)
tk.Button(left, text="Graphs", command=show_graphs, **btn).pack(pady=4)
tk.Button(left, text="Past 5 Minutes", command=show_past_5_minutes, **btn).pack(pady=4)
tk.Button(left, text="Today Usage", command=show_today_usage, **btn).pack(pady=4)
tk.Button(left, text="Save Report", bg="green", fg="white",
          font=("Arial",12,"bold"), width=20, pady=8,
          command=save_report).pack(pady=20)

# ================= START =================
show_live_status()
live_update()
root.mainloop()
conn.close()