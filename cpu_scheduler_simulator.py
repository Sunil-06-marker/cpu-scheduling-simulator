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

# ------------------------------------------------------------
# Dashboard UI (CustomTkinter)
# ------------------------------------------------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class DashboardApp:
    """Main application class for the CPU scheduler dashboard."""

    def __init__(self, root):
        self.root = root
        self.root.title("Intelligent CPU Scheduler — Dashboard")
        self.root.geometry("1400x820")

        self.processes = []
        self._build_ui()

    # --------------------------------------------------------
    # UI Construction
    # --------------------------------------------------------

    def _build_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content_area()

    # -------------- Sidebar -----------------

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.root, width=320, corner_radius=8)
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=(14, 8), pady=14)
        self.sidebar.grid_propagate(False)

        title = ctk.CTkLabel(self.sidebar, text="Process Input",
                             font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(anchor="w", padx=12, pady=(8, 6))

        self._build_input_form()
        self._build_buttons()
        self._build_settings_card()

    def _build_input_form(self):
        form = ctk.CTkFrame(self.sidebar, fg_color="#2a2a2a", corner_radius=8)
        form.pack(fill="x", padx=12, pady=(6, 12))

        labels = ["PID", "Arrival Time", "Burst Time", "Priority"]
        entries = []

        for i, label in enumerate(labels):
            ctk.CTkLabel(form, text=label).grid(row=i, column=0, sticky="w",
                                                padx=10, pady=(6, 6))
            entry = ctk.CTkEntry(form, width=200)
            entry.grid(row=i, column=1, padx=10, pady=(6, 6))
            entries.append(entry)

        self.entry_pid, self.entry_arr, self.entry_burst, self.entry_pr = entries

    def _build_buttons(self):
        ctk.CTkButton(self.sidebar, text="Add Process",
                      fg_color="#00c389", command=self.add_process)\
            .pack(fill="x", padx=12, pady=(4, 6))

        ctk.CTkButton(self.sidebar, text="Clear All",
                      fg_color="#e85d5d", command=self.clear_processes)\
            .pack(fill="x", padx=12, pady=(0, 12))

    def _build_settings_card(self):
        card = ctk.CTkFrame(self.sidebar, corner_radius=8, fg_color="#232323")
        card.pack(fill="x", padx=12, pady=(4, 12))

        ctk.CTkLabel(card, text="Scheduling Settings",
                     font=ctk.CTkFont(size=14, weight="bold"))\
            .grid(row=0, column=0, columnspan=2, padx=10, pady=(8, 6))

        ctk.CTkLabel(card, text="Algorithm").grid(row=1, column=0,
                                                  padx=10, pady=6, sticky="w")
        self.algo_opt = ctk.CTkOptionMenu(card, values=[
            "FCFS", "SJF", "Priority", "Round Robin"
        ])
        self.algo_opt.grid(row=1, column=1, padx=10, pady=6)
        self.algo_opt.set("FCFS")
        self.algo_opt.configure(command=self._on_algo_change)

        ctk.CTkLabel(card, text="Time Quantum").grid(row=2, column=0,
                                                     padx=10, pady=6, sticky="w")
        self.entry_quantum = ctk.CTkEntry(card, width=120, placeholder_text="e.g. 2")
        self.entry_quantum.grid(row=2, column=1, padx=10, pady=(6, 12))
        self.entry_quantum.configure(state="disabled")

        ctk.CTkButton(self.sidebar, text="Run Simulation",
                      fg_color="#1976d2", command=self.run_simulation)\
            .pack(fill="x", padx=12, pady=(8, 6))

        ctk.CTkButton(self.sidebar, text="Reset Output",
                      fg_color="#ff9800", command=self.reset_output)\
            .pack(fill="x", padx=12, pady=(0, 6))

    # -------------- Main Content Area -----------------

    def _build_content_area(self):
        self.content = ctk.CTkFrame(self.root, corner_radius=8)
        self.content.grid(row=0, column=1, sticky="nswe", padx=(8, 14), pady=14)

        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_rowconfigure(2, weight=2)
        self.content.grid_columnconfigure(0, weight=1)

        self._build_process_panel()
        self._build_metrics_panel()
        self._build_gantt_panel()

    def _build_process_panel(self):
        frame = ctk.CTkFrame(self.content, corner_radius=6)
        frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))

        ctk.CTkLabel(frame, text="Process List",
                     font=ctk.CTkFont(size=16, weight="bold"))\
            .pack(anchor="w", padx=8, pady=(8, 6))

        self._make_treeview(frame,
                            ["PID", "Arrival", "Burst", "Priority"],
                            height=6, assign_to="proc_tree")\
            .pack(fill="both", expand=True, padx=8, pady=(6, 12))

    def _build_metrics_panel(self):
        frame = ctk.CTkFrame(self.content, corner_radius=6)
        frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)

        ctk.CTkLabel(frame, text="Metrics",
                     font=ctk.CTkFont(size=16, weight="bold"))\
            .pack(anchor="w", padx=8, pady=(8, 6))

        self._make_treeview(frame,
                            ["PID", "CT", "TAT", "WT", "RT"],
                            height=4, assign_to="metrics_tree")\
            .pack(fill="both", expand=True, padx=8, pady=(6, 12))

        self.summary_label = ctk.CTkLabel(frame, text="Summary:")
        self.summary_label.pack(anchor="w", padx=8, pady=(4, 8))

    def _build_gantt_panel(self):
        frame = ctk.CTkFrame(self.content, corner_radius=6)
        frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(6, 12))

        ctk.CTkLabel(frame, text="Gantt Chart",
                     font=ctk.CTkFont(size=16, weight="bold"))\
            .pack(anchor="w", padx=8, pady=(8, 6))

        self.fig = Figure(figsize=(10, 4), dpi=110, facecolor="#1b1b1b")
        self.ax = self.fig.add_subplot(111)

        self.ax.set_facecolor("#1b1b1b")
        self.ax.tick_params(colors="#cfcfcf")
        self.ax.spines['bottom'].set_color("#555")
        self.ax.spines['left'].set_color("#555")

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(6, 12))



    # --------------------------------------------------------
    # Treeview Utility
    # --------------------------------------------------------

    def _make_treeview(self, parent, columns, height, assign_to=None):
        container = tk.Frame(parent, bg="#222")
        style = ttk.Style()

        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        background="#2a2a2a",
                        foreground="#e6e6e6",
                        fieldbackground="#2a2a2a",
                        rowheight=26)
        style.configure("Custom.Treeview.Heading",
                        background="#2a2a2a",
                        foreground="#ffffff")

        tree = ttk.Treeview(container, columns=columns,
                            show="headings", height=height,
                            style="Custom.Treeview")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center")

        scrollbar = ttk.Scrollbar(container, orient="vertical",
                                  command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if assign_to == "proc_tree":
            self.proc_tree = tree
        elif assign_to == "metrics_tree":
            self.metrics_tree = tree

        return container

    # --------------------------------------------------------
    # Event Handlers
    # --------------------------------------------------------

    def _on_algo_change(self, choice):
        if choice == "Round Robin":
            self.entry_quantum.configure(state="normal")
        else:
            self.entry_quantum.configure(state="disabled")
            self.entry_quantum.delete(0, tk.END)

    def add_process(self):
        pid = self.entry_pid.get().strip()
        arr = self.entry_arr.get().strip()
        burst = self.entry_burst.get().strip()
        pr = self.entry_pr.get().strip()

        if not pid or not arr or not burst:
            messagebox.showwarning("Input Error", "PID, Arrival, and Burst are required.")
            return

        try:
            arr_i = int(arr)
            burst_i = int(burst)
            pr_i = int(pr) if pr else 0

            if arr_i < 0 or burst_i <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values.")
            return

        process = Process(pid, arr_i, burst_i, pr_i)
        self.processes.append(process)

        self.proc_tree.insert("", "end", values=(pid, arr_i, burst_i, pr_i))

        self.entry_pid.delete(0, tk.END)
        self.entry_arr.delete(0, tk.END)
        self.entry_burst.delete(0, tk.END)
        self.entry_pr.delete(0, tk.END)

    def clear_processes(self):
        self.processes = []
        for item in self.proc_tree.get_children():
            self.proc_tree.delete(item)
        for item in self.metrics_tree.get_children():
            self.metrics_tree.delete(item)

        self.summary_label.configure(text="Summary:")
        self._clear_gantt()

    def reset_output(self):
        for item in self.metrics_tree.get_children():
            self.metrics_tree.delete(item)
        self.summary_label.configure(text="Summary:")
        self._clear_gantt()

    def _clear_gantt(self):
        self.ax.clear()
        self.ax.set_facecolor("#1b1b1b")
        self.canvas.draw()

    def run_simulation(self):
        algo = self.algo_opt.get()
        quantum = None

        if algo == "Round Robin":
            qtxt = self.entry_quantum.get().strip()
            if not qtxt:
                messagebox.showerror("Missing Quantum", "Please enter a time quantum.")
                return

            try:
                quantum = int(qtxt)
                if quantum <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Quantum", "Quantum must be a positive integer.")
                return

        gantt, metrics, summary = run_scheduler(self.processes, algo, quantum)

        for item in self.metrics_tree.get_children():
            self.metrics_tree.delete(item)

        for pid, m in metrics.items():
            self.metrics_tree.insert("", "end",
                                     values=(pid, m["CT"], m["TAT"], m["WT"], m["RT"]))

        self.summary_label.configure(
            text=f"Summary:  Avg WT={summary['avg_wt']:.2f} | "
                 f"Avg TAT={summary['avg_tat']:.2f} | "
                 f"Throughput={summary['throughput']:.3f} | "
                 f"Total Time={summary['total_time']}"
        )

        self._draw_gantt(gantt)

    def _draw_gantt(self, gantt):
        self.ax.clear()
        self.ax.set_facecolor("#1b1b1b")

        # Assign colors to processes
        pids = [b["pid"] for b in gantt if b["pid"] != "IDLE"]
        unique = list(dict.fromkeys(pids))

        palette = [
            "#00b894", "#0984e3", "#6c5ce7", "#e84393",
            "#fdcb6e", "#e17055", "#00cec9", "#e056fd"
        ]

        colors = {pid: palette[i % len(palette)] for i, pid in enumerate(unique)}

        y = 0.6

        for block in gantt:
            pid = block["pid"]
            start, end = block["start"], block["end"]
            width = end - start
            color = "#555" if pid == "IDLE" else colors.get(pid, "#999")

            self.ax.barh(y, width, left=start, height=0.6,
                         color=color, edgecolor="white", linewidth=0.6)

            if width >= 0.6:
                self.ax.text(start + width / 2, y, pid,
                             ha="center", va="center",
                             fontsize=9, color="#0b0b0b", weight="bold")

        total = gantt[-1]["end"] if gantt else 1
        xticks = list(range(0, int(math.ceil(total)) + 1))

        self.ax.set_xticks(xticks)
        self.ax.set_yticks([])
        self.ax.tick_params(colors="#d0d0d0")

        self.ax.xaxis.grid(True, color="#2b2b2b")

        self.canvas.draw()

