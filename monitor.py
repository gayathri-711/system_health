# -------------------------------
# FILE NAME: monitor.py
# -------------------------------

import psutil
import sqlite3
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

# ---------- DATABASE SETUP ----------
conn = sqlite3.connect("system_health.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS system_health (
    timestamp TEXT,
    cpu REAL,
    memory REAL,
    disk REAL
)
""")
conn.commit()

# ---------- DATA STORAGE ----------
cpu_data = deque(maxlen=20)
mem_data = deque(maxlen=20)
disk_data = deque(maxlen=20)

# ---------- DASHBOARD SETUP ----------
fig = plt.figure(figsize=(12, 6))
fig.suptitle("LIVE SYSTEM HEALTH MONITORING DASHBOARD", fontsize=16, fontweight="bold")

ax1 = plt.subplot(2, 2, 1)
ax2 = plt.subplot(2, 2, 2)
ax3 = plt.subplot(2, 2, 3)
ax4 = plt.subplot(2, 2, 4)

# ---------- EXPORT REPORT FUNCTION ----------
def export_csv_report():
    cur.execute("SELECT * FROM system_health")
    rows = cur.fetchall()

    with open("system_health_report.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "CPU (%)", "Memory (%)", "Disk (%)"])
        writer.writerows(rows)

    print("✅ Report exported: system_health_report.csv")

# ---------- LIVE UPDATE FUNCTION ----------
def update(frame):
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Store in DB
    cur.execute(
        "INSERT INTO system_health VALUES (?, ?, ?, ?)",
        (time_now, cpu, memory, disk)
    )
    conn.commit()

    cpu_data.append(cpu)
    mem_data.append(memory)
    disk_data.append(disk)

    ax1.clear()
    ax2.clear()
    ax3.clear()
    ax4.clear()

    ax1.plot(cpu_data, marker='o')
    ax1.set_ylim(0, 100)
    ax1.set_title("CPU Usage (%)")

    ax2.plot(mem_data, marker='o')
    ax2.set_ylim(0, 100)
    ax2.set_title("Memory Usage (%)")

    ax3.plot(disk_data, marker='o')
    ax3.set_ylim(0, 100)
    ax3.set_title("Disk Usage (%)")

    # System status
    status = "NORMAL"
    color = "green"
    if cpu > 80 or memory > 80 or disk > 80:
        status = "CRITICAL"
        color = "red"

    ax4.axis("off")
    ax4.text(
        0.5, 0.5,
        f"SYSTEM STATUS\n{status}",
        fontsize=18,
        ha='center',
        va='center',
        bbox=dict(boxstyle="round", facecolor=color)
    )

# ---------- AUTO REFRESH ----------
ani = FuncAnimation(fig, update, interval=2000)

# ---------- EXPORT REPORT ON CLOSE ----------
plt.show()
export_csv_report()

conn.close()