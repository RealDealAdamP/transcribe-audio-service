# File: gui/queue_display.py

import os
import tkinter as tk
import ttkbootstrap as ttk

class QueueFrame(ttk.LabelFrame):
    def __init__(self, parent, on_select_file_callback, on_double_click_file_callback, on_refresh_click=None, styles=None, **kwargs):
        super().__init__(parent, text="", bootstyle=styles["queue"]["frame"], padding=10, **kwargs)
        self.styles = styles

        # ────────────────
        # Top-Left Refresh Button (now in col 0)
        if on_refresh_click:
            ttk.Button(self, text="⟳",bootstyle=styles["queue"]["button_refresh"], width=3, command=on_refresh_click).grid(row=0, column=0, sticky="nw", padx=5, pady=5)

        # ────────────────
        # Labels (start from col 1)
        ttk.Label(self, text="Transcribe Queue:", bootstyle=styles["queue"]["label_queue"]).grid(row=0, column=1, sticky="w")
        ttk.Label(self, text="Status:", bootstyle=styles["queue"]["label_status"]).grid(row=0, column=2, sticky="w")
        ttk.Label(self, text="Output Text:", bootstyle=styles["queue"]["label_output_txt"]).grid(row=0, column=4, sticky="w")

        # ────────────────
        # Listboxes
        self.listbox_queue = tk.Listbox(self, width=40, height=10)
        self.listbox_queue.grid(row=1, column=1, padx=5, pady=5)
        self.listbox_queue.bind("<Double-1>", on_double_click_file_callback)
        self.listbox_queue.bind("<<ListboxSelect>>", on_select_file_callback)

        self.status_queue = tk.Listbox(self, width=15, height=10)
        self.status_queue.grid(row=1, column=2, padx=5, pady=5)

        # Shared scrollbar (col 3)
        scrollbar = ttk.Scrollbar(self, orient="vertical")
        scrollbar.config(command=lambda *args: (self.listbox_queue.yview(*args), self.status_queue.yview(*args)))
        scrollbar.grid(row=1, column=3, sticky="ns")

        self.listbox_queue.config(yscrollcommand=scrollbar.set)
        self.status_queue.config(yscrollcommand=scrollbar.set)

        # Output Box (col 4)
        output_frame = ttk.Frame(self)
        output_frame.grid(row=1, column=4, padx=5, pady=5, sticky="nsew")

        self.output_box = tk.Text(output_frame, wrap="word", width=60, height=10, state="disabled")
        self.output_box.pack(side="left", fill="both", expand=True)

        output_scroll = ttk.Scrollbar(output_frame, command=self.output_box.yview)
        output_scroll.pack(side="right", fill="y")
        self.output_box.config(yscrollcommand=output_scroll.set)

    def get_queue_widgets(self):
        return self.listbox_queue, self.status_queue, self.output_box
