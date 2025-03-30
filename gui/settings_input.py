# File: gui/settings_input.py

import tkinter as tk
import ttkbootstrap as ttk
from tkinter import filedialog
from services.constants import LANGUAGE_MAP


class SettingsInputFrame(ttk.LabelFrame):
    def __init__(self, parent, input_dir_var, language_var,monitoring_enabled_var, monitoring_interval_var, styles, label_font=None,browse_callback=None, **kwargs):
        super().__init__(parent, text="Input Settings", bootstyle=styles["input"]["frame"], **kwargs)

        self.columnconfigure(0, weight=1)

        self.input_dir_var = input_dir_var
        self.language_var = language_var
        self.monitoring_enabled_var = monitoring_enabled_var
        self.monitoring_interval_var = monitoring_interval_var
        self.styles = styles
        self.browse_callback = browse_callback 

        # Row 0 – Input Directory Label
        ttk.Label(
            self,
            text="Input Directory:",
            bootstyle=styles["input"]["label_input_dir"],
            font=label_font
        ).grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))

        # Row 1 – Directory Entry + Browse Button
        entry_input = ttk.Entry(
            self,
            textvariable=self.input_dir_var,
            width=50,
            state="readonly",
            bootstyle=styles["input"]["entry_input_dir"]
        )
        entry_input.grid(row=1, column=0, padx=(5, 0), pady=5, sticky="ew")

        ttk.Button(
            self,
            text="Browse",
            command=self.browse_callback,
            bootstyle=styles["input"]["button_browse"]
        ).grid(row=1, column=1, padx=(5, 5), pady=5, sticky="w")

        # Row 2 – Language Label + Monitoring Toggle
        ttk.Label(
            self,
            text="Select Audio Language:",
            bootstyle=styles["input"]["label_lang"],
            font=label_font
        ).grid(row=2, column=0, sticky="w", padx=1, pady=(0, 0))

        ttk.Checkbutton(
            self,
            text="Directory Monitoring",
            variable=self.monitoring_enabled_var,
            bootstyle=styles["input"]["checkbox_monitoring"],
            command=self.toggle_interval_state
        ).grid(row=4, column=0, sticky="w", padx=1, pady=(5, 0))

        # Row 3 – Language Dropdown 
        self.lang_dropdown = ttk.Combobox(
            self,
            values=list(LANGUAGE_MAP.keys()),
            state="readonly",
            bootstyle=styles["input"]["dropdown_lang"]
        )
        self.lang_dropdown.set("English")
        self.lang_dropdown.grid(row=3, column=0, padx=5, pady=(0, 5), sticky="w")
        self.lang_dropdown.bind("<<ComboboxSelected>>", self._on_language_selected)

        ttk.Label(
            self,
            text="Set Interval (minutes):",
            bootstyle=styles["input"]["label_interval"],
            font=label_font
        ).grid(row=5, column=0, sticky="w", padx=5, pady=(0, 2))

        # Row 4 – Shrunk Interval Scale
        self.interval_scale = ttk.Scale(
            self,
            from_=60,
            to=43200,
            length=180,  # ⬅️ Shrink the width
            variable=self.monitoring_interval_var,
            orient="horizontal",
            bootstyle=styles["input"]["scale_interval"],
            command=self.update_interval_txt
        )
        self.interval_scale.grid(row=7, column=0, sticky="w", padx=5, pady=(0, 2))
        self.interval_scale.config(state="disabled")

        # Row 6 – Interval Text (dynamic)
        self.interval_txt = ttk.Label(self, text="Current: 10 min", foreground="#6c757d")  # 🔧 Start in muted gray
        self.interval_txt.grid(row=6, column=0, sticky="w", padx=5, pady=(0, 10))

        # Capture the normal foreground color for later
        self._default_fg_interval_txt = self.interval_txt.cget("foreground") if self.monitoring_enabled_var.get() else "#FFFFFF"
    

    def _on_language_selected(self, event=None):
        selected_lang = self.lang_dropdown.get()
        self.language_var.set(LANGUAGE_MAP.get(selected_lang, ""))

    def set_state(self, state):
        for child in self.winfo_children():
            try:
                child.configure(state=state)
            except tk.TclError:
                pass

    def toggle_interval_state(self):
        if self.monitoring_enabled_var.get():
            state = "normal"
            fg = self._default_fg_interval_txt  # ✅ Restore original color
        else:
            state = "disabled"
            fg = "#6c757d"  # ✅ Muted gray for disabled look

        self.interval_scale.config(state=state)
        self.interval_txt.config(foreground=fg)


    def update_interval_txt(self, value):
        minutes = int(float(value) / 60)
        self.interval_txt.config(text=f"Current: {minutes} min")

    def validate(self):
        if not self.input_dir_var.get():
            tk.messagebox.showerror("Validation Error", "Please select an input directory.")
            return False
        if not self.language_var.get():
            tk.messagebox.showerror("Validation Error", "Please select an audio language.")
            return False
        return True

    def set_output_frame(self, output_frame):
        self.output_frame = output_frame

    def _on_language_selected(self, event=None):
        selected_lang = self.lang_dropdown.get()
        self.language_var.set(LANGUAGE_MAP.get(selected_lang, ""))

        # Notify output settings to update checkbox state
        if hasattr(self, "output_frame"):
            self.output_frame.update_translate_state()
