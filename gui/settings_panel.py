# File: gui/settings_panel.py

import tkinter as tk
import ttkbootstrap as ttk
from gui.style_config import get_bootstyles  #centralized style registry

def create_settings_panel(parent, model_var, lang_var, output_format_var, speaker_var):
    """
    Creates a settings panel with:
    - Whisper model selection
    - Language selection
    - Output format selection
    - Speaker recognition toggle

    Returns:
        settings_frame (ttk.Labelframe)
        model_buttons (List[ttk.Radiobutton])
        lang_buttons (List[ttk.Radiobutton])
        output_buttons (List[ttk.Radiobutton])
        speaker_checkbox (ttk.Checkbutton)
    """
    styles = get_bootstyles()  #Use centralized style tokens

    settings_frame = ttk.Labelframe(
        parent,
        text="Settings",
        padding=10,
        bootstyle=styles["label_settings"]
    )

    # ─────────────────────────────────────────────
    # Whisper model selection
    ttk.Label(
        settings_frame,
        text="Select Whisper Model:",
        bootstyle=styles["label_model"]
    ).grid(row=0, column=0, sticky="w", pady=(5, 0))

    model_frame = ttk.Frame(settings_frame)
    model_frame.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(5, 0))

    model_buttons = []
    for model in ["base", "small", "medium", "large"]:
        btn = ttk.Radiobutton(
            model_frame,
            text=model,
            variable=model_var,
            value=model,
            bootstyle=styles["model_radio"]
        )
        btn.pack(side="left", padx=5)
        model_buttons.append(btn)

    # ─────────────────────────────────────────────
    # Language selection
    ttk.Label(
        settings_frame,
        text="Select Language:",
        bootstyle=styles["label_lang"]
    ).grid(row=1, column=0, sticky="w", pady=(10, 0))

    lang_frame = ttk.Frame(settings_frame)
    lang_frame.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(10, 0))

    lang_buttons = []
    for lang, code in {"English": "en", "Spanish": "es", "French": "fr"}.items():
        btn = ttk.Radiobutton(
            lang_frame,
            text=lang,
            variable=lang_var,
            value=code,
            bootstyle=styles["lang_radio"]
        )
        btn.pack(side="left", padx=5)
        lang_buttons.append(btn)

    # ─────────────────────────────────────────────
    # Output format radio buttons
    ttk.Label(
        settings_frame,
        text="Select Output Format:",
        bootstyle=styles["label_output"]
    ).grid(row=2, column=0, sticky="w", pady=(10, 0))

    output_frame = ttk.Frame(settings_frame)
    output_frame.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(10, 0))

    output_buttons = []
    for out in ["txt", "json", "csv", "xml"]:
        btn = ttk.Radiobutton(
            output_frame,
            text=out,
            variable=output_format_var,
            value=out,
            bootstyle=styles["output_radio"]
        )
        btn.pack(side="left", padx=5)
        output_buttons.append(btn)

    # ─────────────────────────────────────────────
    # Speaker recognition toggle
    ttk.Label(
        settings_frame,
        text="Options:",
        bootstyle=styles["label_options"]
    ).grid(row=3, column=0, sticky="w", pady=(10, 0))

    speaker_checkbox = ttk.Checkbutton(
        settings_frame,
        text="Enable Automated Speaker Recognition",
        variable=speaker_var,
        bootstyle=styles["speaker_toggle"]
    )
    speaker_checkbox.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=(10, 0))

    return settings_frame, model_buttons, lang_buttons, output_buttons, speaker_checkbox
