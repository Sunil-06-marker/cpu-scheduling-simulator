"""
cpu_scheduler_dashboard.py

Dashboard-based CPU Scheduling Simulator supporting:
- FCFS
- SJF (Non-preemptive)
- Priority Scheduling (Non-preemptive)
- Round Robin

Built using:
    - customtkinter (modern GUI)
    - matplotlib (Gantt chart visualization)

Run:
    python cpu_scheduler_dashboard.py
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ------------------------------------------------------------
# Data Model
# ------------------------------------------------------------

class Process:
    """
    Simple container for process attributes:
        pid: Process ID (string)
        arrival: Arrival time (int)
        burst: CPU burst time (int)
        priority: Smaller value = higher priority (int)
    """
    def __init__(self, pid, arrival, burst, priority=0):
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.priority = priority
