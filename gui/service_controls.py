# File: gui/service_controls.py

import ttkbootstrap as ttk

class ServiceControlsFrame(ttk.Frame):
    def __init__(self, parent, on_start, on_stop, styles, **kwargs):
        super().__init__(parent, **kwargs)
        self.styles = styles

        # Transcribe Button
        btn_transcribe = ttk.Button(
            self,
            text="Transcribe",
            command=on_start,
            bootstyle=styles["controls"]["button_transcribe"]
        )
        btn_transcribe.pack(side="left", padx=(0, 10))

        # Stop Button
        btn_stop = ttk.Button(
            self,
            text="Stop",
            command=on_stop,
            bootstyle=styles["controls"]["button_stop"]
        )
        btn_stop.pack(side="left", padx=(0, 10))

        # Status Label
        self.status_label = ttk.Label(
            self,
            text="Service is currently Stopped",
            bootstyle=styles["controls"]["label_status"]
        )
        self.status_label.pack(side="left", padx=(10, 0))

    def get_status_label(self):
        return self.status_label
