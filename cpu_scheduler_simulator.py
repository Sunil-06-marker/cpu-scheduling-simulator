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


# ------------------------------------------------------------
# Scheduling Algorithms
# ------------------------------------------------------------

def simulate_fcfs(processes):
    """First Come First Serve (Non-preemptive)."""
    processes = sorted(processes, key=lambda p: p.arrival)
    gantt = []
    time = 0

    for p in processes:
        if time < p.arrival:
            gantt.append({"pid": "IDLE", "start": time, "end": p.arrival})
            time = p.arrival

        start = time
        end = time + p.burst
        gantt.append({"pid": p.pid, "start": start, "end": end})
        time = end

    return gantt


def simulate_sjf_np(processes):
    """Shortest Job First (Non-preemptive)."""
    remaining = sorted(processes, key=lambda p: p.arrival)
    gantt = []
    time = 0

    while remaining:
        ready = [p for p in remaining if p.arrival <= time]

        if not ready:
            next_arrival = remaining[0].arrival
            gantt.append({"pid": "IDLE", "start": time, "end": next_arrival})
            time = next_arrival
            continue

        p = min(ready, key=lambda x: x.burst)
        remaining.remove(p)

        start = time
        end = time + p.burst
        gantt.append({"pid": p.pid, "start": start, "end": end})
        time = end

    return gantt


def simulate_priority_np(processes):
    """Non-preemptive Priority Scheduling."""
    remaining = sorted(processes, key=lambda p: p.arrival)
    gantt = []
    time = 0

    while remaining:
        ready = [p for p in remaining if p.arrival <= time]

        if not ready:
            next_arrival = remaining[0].arrival
            gantt.append({"pid": "IDLE", "start": time, "end": next_arrival})
            time = next_arrival
            continue

        p = min(ready, key=lambda x: (x.priority, x.arrival))
        remaining.remove(p)

        start = time
        end = time + p.burst
        gantt.append({"pid": p.pid, "start": start, "end": end})
        time = end

    return gantt


def simulate_rr(processes, quantum):
    """Round Robin scheduling."""
    if quantum <= 0:
        raise ValueError("Quantum must be > 0")

    processes = sorted(processes, key=lambda p: p.arrival)
    gantt = []
    time = 0

    remaining = {p.pid: p.burst for p in processes}
    first_start = {p.pid: None for p in processes}

    ready = []
    idx = 0

    def add_arrivals(current_time):
        nonlocal idx
        while idx < len(processes) and processes[idx].arrival <= current_time:
            ready.append(processes[idx])
            idx += 1

    add_arrivals(time)

    while ready or idx < len(processes):
        if not ready:
            next_arrival = processes[idx].arrival
            gantt.append({"pid": "IDLE", "start": time, "end": next_arrival})
            time = next_arrival
            add_arrivals(time)
            continue

        p = ready.pop(0)

        if first_start[p.pid] is None:
            first_start[p.pid] = time

        run_time = min(quantum, remaining[p.pid])
        start, end = time, time + run_time
        gantt.append({"pid": p.pid, "start": start, "end": end})

        time = end
        remaining[p.pid] -= run_time

        add_arrivals(time)

        if remaining[p.pid] > 0:
            ready.append(p)

    return gantt


# ------------------------------------------------------------
# Metrics Calculation
# ------------------------------------------------------------

def compute_metrics(processes, gantt):
    """Returns individual process metrics and overall summary."""

    pids = [p.pid for p in processes]
    arrival = {p.pid: p.arrival for p in processes}
    burst = {p.pid: p.burst for p in processes}

    completion = {pid: 0 for pid in pids}
    first_start = {pid: None for pid in pids}

    for block in gantt:
        pid = block["pid"]
        if pid == "IDLE":
            continue

        start, end = block["start"], block["end"]
        completion[pid] = max(completion[pid], end)

        if first_start[pid] is None or start < first_start[pid]:
            first_start[pid] = start

    metrics = {}
    total_wt = total_tat = 0

    for pid in pids:
        ct = completion[pid]
        tat = ct - arrival[pid]
        wt = tat - burst[pid]
        rt = (first_start[pid] - arrival[pid]) if first_start[pid] is not None else 0

        metrics[pid] = {"CT": ct, "TAT": tat, "WT": wt, "RT": rt}

        total_wt += wt
        total_tat += tat

    total_time = gantt[-1]["end"] if gantt else 0
    summary = {
        "avg_wt": total_wt / len(pids),
        "avg_tat": total_tat / len(pids),
        "throughput": len(pids) / total_time if total_time else 0,
        "total_time": total_time
    }

    return metrics, summary


def run_scheduler(processes, algo, quantum=None):
    """Main routing function for selecting algorithms."""
    if algo == "FCFS":
        gantt = simulate_fcfs(processes)
    elif algo == "SJF":
        gantt = simulate_sjf_np(processes)
    elif algo == "Priority":
        gantt = simulate_priority_np(processes)
    elif algo == "Round Robin":
        gantt = simulate_rr(processes, quantum)
    else:
        raise ValueError("Unknown scheduling algorithm.")

    metrics, summary = compute_metrics(processes, gantt)
    return gantt, metrics, summary
