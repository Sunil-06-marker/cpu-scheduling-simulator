CPU Scheduler Simulator

A modern dashboard-style simulator for CPU scheduling algorithms with real-time visualization.

Requirements

Python 3.8+

Libraries:

pip install customtkinter matplotlib

How to Run
python cpu_scheduler_dashboard.py

Features

Supports FCFS, SJF, Priority, Round Robin

Process input: PID, Arrival, Burst, Priority

Real-time Gantt Chart

Metrics: CT, TAT, WT, RT, Averages, Throughput

Modern dark dashboard UI

Project Structure
cpu_scheduler_dashboard.py
README.md

Usage

Add processes in the left panel

Select scheduling algorithm

For RR, enter a time quantum

Click Run Simulation

Future Improvements

Preemptive algorithms

Export results (CSV/PDF)

Animation mode
