# File: gui/service_controls.py

import ttkbootstrap as ttk
import time

class ServiceControlsFrame(ttk.Frame):
    def __init__(self, parent, on_start, on_stop, styles, **kwargs):
        super().__init__(parent, **kwargs)
        self.styles = styles

        # Subframe for the button row
        self.button_row = ttk.Frame(self)
        self.button_row.pack(side="top", fill="x", pady=(0, 5))

        # Transcribe Button
        btn_transcribe = ttk.Button(
            self.button_row,
            text="Transcribe",
            command=on_start,
            bootstyle=styles["controls"]["button_transcribe"]
        )
        btn_transcribe.pack(side="left", padx=(0, 10))

        # Stop Button
        btn_stop = ttk.Button(
            self.button_row,
            text="Stop",
            command=on_stop,
            bootstyle=styles["controls"]["button_stop"]
        )
        btn_stop.pack(side="left", padx=(0, 10))

        # Status Label
        self.status_label = ttk.Label(
            self.button_row,
            text="Service is currently Stopped",
            bootstyle=styles["controls"]["label_status"]
        )
        self.status_label.pack(side="left", padx=(10, 0))

        #Latest Service Timer 
        self.start_time = None
        self.timer_after_id = None

        # Latest Service Timer (main frame, below button row)
        self.latest_duration_label = ttk.Label(self, text="⟳ Latest Service Duration: --:--", style="info.TLabel")
        self.latest_duration_label.pack(side="top", anchor="w", padx=(5, 0))

    def get_status_label(self):
        return self.status_label
    
    def update_service_timer(self):
        if self.start_time is not None:
            elapsed = int(time.time() - self.start_time)
            minutes, seconds = divmod(elapsed, 60)
            self.latest_duration_label.config(text=f"⟳ Latest Service Duration: {minutes:02}:{seconds:02}")
            self.timer_after_id = self.after(1000, self.update_service_timer)

    def stop_service_timer(self):
        if self.timer_after_id:
            self.after_cancel(self.timer_after_id)
            self.timer_after_id = None
        self.start_time = None