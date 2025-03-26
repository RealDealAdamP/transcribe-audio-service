# File: gui/button_controls.py

import ttkbootstrap as ttk
from gui.style_config import get_bootstyles  #Centralized styling

def create_button_controls(parent, on_start, on_stop):
    """
    Creates the bottom row of controls: Transcribe, Stop, and Status label.

    Args:
        parent (tk.Widget): The parent container (usually root)
        on_start (function): Callback for Transcribe button
        on_stop (function): Callback for Stop button

    Returns:
        Tuple[ttk.Frame, ttk.Label]: The control frame and status label widget
    """
    styles = get_bootstyles()  #Load style tokens
    frame = ttk.Frame(parent)

    btn_transcribe = ttk.Button(
        frame, 
        text="Transcribe", 
        command=on_start, 
        bootstyle=styles["button_transcribe"]
    )
    btn_transcribe.pack(side="left", padx=(0, 10))

    btn_stop = ttk.Button(
        frame, 
        text="Stop", 
        command=on_stop, 
        bootstyle=styles["button_stop"]
    )
    btn_stop.pack(side="left", padx=(0, 10))

    status_label = ttk.Label(
        frame, 
        text="Service is currently Stopped", 
        bootstyle=styles["label_status"]
    )
    status_label.pack(side="left", padx=(10, 0))

    return frame, status_label
