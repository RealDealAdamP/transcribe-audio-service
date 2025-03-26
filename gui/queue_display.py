# File: gui/queue_display.py

import os
import tkinter as tk
import ttkbootstrap as ttk
from gui.style_config import get_bootstyles  # ✅ Centralized style tokens

def create_queue_display(parent, on_select_file_callback, on_double_click_file_callback):
    """
    Creates the queue display section with:
    - List of audio files
    - Status indicators
    - Transcription output box

    Args:
        parent (tk.Widget): The parent container (usually root or a frame)
        on_select_file_callback (function): Function to call when a file is selected

    Returns:
        Tuple: (frame, listbox_queue, status_queue, output_box)
    """
    styles = get_bootstyles()  # ✅ Load bootstyle tokens
    frame = ttk.Frame(parent)

    # Labels
    ttk.Label(frame, text="Transcribe Queue:", bootstyle=styles["label_queue"]).grid(row=0, column=0, sticky="w")
    ttk.Label(frame, text="Status:", bootstyle=styles["label_status"]).grid(row=0, column=1, sticky="w")
    ttk.Label(frame, text="Output Text:", bootstyle=styles["label_output_txt"]).grid(row=0, column=3, sticky="w")

    # Listboxes
    listbox_queue = tk.Listbox(frame, width=40, height=10)
    listbox_queue.grid(row=1, column=0, padx=5, pady=5)
    listbox_queue.bind("<Double-1>", on_double_click_file_callback)

    status_queue = tk.Listbox(frame, width=15, height=10)
    status_queue.grid(row=1, column=1, padx=5, pady=5)

    # Shared scrollbar
    scrollbar = ttk.Scrollbar(frame, orient="vertical")
    scrollbar.config(command=lambda *args: (listbox_queue.yview(*args), status_queue.yview(*args)))
    scrollbar.grid(row=1, column=2, sticky="ns")

    listbox_queue.config(yscrollcommand=scrollbar.set)
    status_queue.config(yscrollcommand=scrollbar.set)

    # Output File Text Box
    output_frame = ttk.Frame(frame)
    output_frame.grid(row=1, column=3, padx=5, pady=5, sticky="nsew")

    output_box = tk.Text(output_frame, wrap="word", width=60, height=10)
    output_box.pack(side="left", fill="both", expand=True)

    output_scroll = ttk.Scrollbar(output_frame, command=output_box.yview)
    output_scroll.pack(side="right", fill="y")
    output_box.config(yscrollcommand=output_scroll.set)

    # Bind file selection to provided callback
    listbox_queue.bind("<<ListboxSelect>>", on_select_file_callback)

    return frame, listbox_queue, status_queue, output_box
