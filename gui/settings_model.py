# File: gui/settings_model.py

import ttkbootstrap as ttk
import tkinter as tk

class SettingsModelFrame(ttk.LabelFrame):
    def __init__(self, parent, model_var, speaker_recognition_var, styles, label_font=None, **kwargs):
        super().__init__(parent, text="Model Settings", bootstyle=styles["model"]["frame"], **kwargs)

        self.model_var = model_var
        self.speaker_recognition_var = speaker_recognition_var
        self.styles = styles

        # Label for Whisper Model
        ttk.Label(
            self,
            text="Select Whisper Model:",
            bootstyle=styles["model"]["label_model"],
            font=label_font
        ).grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))


        
        # Sub-frame to group radio buttons
        model_frame = ttk.Frame(self)
        model_frame.grid(row=1, column=0, columnspan=5, sticky="w", padx=5, pady=2)
        
        # Radio Buttons for model selection
        self.model_buttons = []
        for idx, model in enumerate(["tiny", "base", "small", "medium", "large"]):
            btn = ttk.Radiobutton(
                model_frame,
                text=model.capitalize(),
                variable=self.model_var,
                value=model,
                bootstyle=styles["model"]["radio_model"]
            )
            btn.pack(side="left", padx=5)
            self.model_buttons.append(btn)

        # Speaker recognition checkbox
        self.checkbox = ttk.Checkbutton(
            self,
            text="Enable Speaker Recognition",
            variable=self.speaker_recognition_var,
            bootstyle=styles["model"]["checkbox_speaker"]
        )
        self.checkbox.grid(row=2, column=0, columnspan=5, sticky="w", padx=5, pady=(10, 5))

    def set_state(self, state):
        for btn in self.model_buttons:
            btn.config(state=state)
        self.checkbox.config(state=state)

    def validate(self):
        # Placeholder for future validation logic (e.g., restrict large models without GPU)
        return True
