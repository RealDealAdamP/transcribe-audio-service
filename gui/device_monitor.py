# File: gui/device_monitor.py

import ttkbootstrap as ttk
from ttkbootstrap.widgets import Meter
import tkinter as tk
from services.utils_device import get_cpu_usage, get_gpu_usage, get_ram_usage
import psutil

try:
    import pynvml
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except:
    GPU_AVAILABLE = False


class DeviceMonitorFrame(ttk.LabelFrame):
    def __init__(self, master=None, styles=None, **kwargs):
        super().__init__(master, text="Device Monitor", bootstyle=styles["monitor"]["frame"], **kwargs)
        self.styles = styles

        # CPU Meter + Labels
        self.cpu_meter = Meter(
            self,
            bootstyle=self.styles["monitor"]["low"],
            metersize=75,
            amountused=0,
            amounttotal=100,
            amountformat="{:.0f}%",
            metertype="full",
            textfont="-size 10 -weight bold",
            subtext=None,
            subtextfont=None,
            showtext=True
        )
        self.cpu_label_top = ttk.Label(self, text="", font=("Helvetica", 8), bootstyle=self.styles["monitor"]["low"])
        self.cpu_label_bottom = ttk.Label(self, text="", font=("Helvetica", 8), bootstyle=self.styles["monitor"]["low"])

        # GPU Meter + Labels
        self.gpu_meter = Meter(
            self,
            bootstyle=self.styles["monitor"]["low"],
            metersize=75,
            amountused=0,
            amounttotal=100,
            amountformat="{:.0f}%",
            metertype="full",
            textfont="-size 10 -weight bold",
            subtext=None,
            subtextfont=None,
            showtext=True
        )
        self.gpu_label_top = ttk.Label(self, text="", font=("Helvetica", 8), bootstyle=self.styles["monitor"]["low"])
        self.gpu_label_bottom = ttk.Label(self, text="", font=("Helvetica", 8), bootstyle=self.styles["monitor"]["low"])

        # Memory Meter + Label
        self.memory_meter = Meter(
            self,
            bootstyle=self.styles["monitor"]["low"],
            metersize=75,
            amountused=0,
            amounttotal=100,
            amountformat="{:.0f}%",
            metertype="full",
            textfont="-size 10 -weight bold",
            subtext=None,
            subtextfont=None,
            showtext=True
        )
        self.memory_label = ttk.Label(self, text="", font=("Helvetica", 8), bootstyle=self.styles["monitor"]["low"])

        # Layout
        self.cpu_meter.grid(row=0, column=0, padx=5, pady=(5, 0))
        self.cpu_label_top.grid(row=1, column=0, padx=5, pady=0)
        self.cpu_label_bottom.grid(row=2, column=0, padx=5, pady=(0, 5))

        self.gpu_meter.grid(row=0, column=1, padx=5, pady=(5, 0))
        self.gpu_label_top.grid(row=1, column=1, padx=5, pady=0)
        self.gpu_label_bottom.grid(row=2, column=1, padx=5, pady=(0, 5))

        self.memory_meter.grid(row=0, column=2, padx=5, pady=(5, 0))
        self.memory_label.grid(row=1, column=2, padx=5, pady=(0, 5))

        self.refresh_meters()

    def refresh_meters(self):
        # CPU
        cpu_info = get_cpu_usage()
        cpu_pct = cpu_info["cpu_percent"]
        self.cpu_meter.configure(amountused=cpu_pct)
        self.cpu_label_top.configure(text=f"CPU: {cpu_info['cpu_name']}")
        self.cpu_label_bottom.configure(text=f"Cores: {cpu_info['cpu_cores']}")
        self._set_style(self.cpu_meter, cpu_pct)

        # GPU
        gpu_info = get_gpu_usage()
        if gpu_info:
            self.gpu_meter.configure(amountused=gpu_info['gpu_percent'])
            self.gpu_label_top.configure(text=f"GPU: {gpu_info['gpu_name']}")
            self.gpu_label_bottom.configure(text=f"VRAM: {gpu_info['mem_used']:.1f} / {gpu_info['mem_total']:.0f} GB    Temp: {gpu_info['gpu_temp']}°C")
            self._set_style(self.gpu_meter, gpu_info['gpu_percent'])
        else:
            self.gpu_meter.configure(amountused=0, bootstyle=self.styles["monitor"]["inactive"])
            self.gpu_label_top.configure(text="GPU: Unavailable", bootstyle=self.styles["monitor"]["inactive"])
            self.gpu_label_bottom.configure(text="")

        # Memory
        ram_pct, ram_used, ram_total = get_ram_usage()
        self.memory_meter.configure(amountused=ram_pct)
        self.memory_label.configure(text=f"Memory: {ram_used:.1f} / {ram_total:.0f} GB")
        self._set_style(self.memory_meter, ram_pct)

        # Repeat after delay
        self.after(1000, self.refresh_meters)

    def _set_style(self, meter, percent):
        if percent < 75:
            meter.configure(bootstyle=self.styles["monitor"]["low"])
        else:
            meter.configure(bootstyle=self.styles["monitor"]["high"])

            
