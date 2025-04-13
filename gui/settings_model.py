# File: gui/settings_model.py

import ttkbootstrap as ttk
import torch
from cfg.conf_main import WHISPER_MODELS, MODEL_VRAM_REQUIREMENTS


class SettingsModelFrame(ttk.LabelFrame):
    def __init__(self, parent, speaker_identification_var, styles, label_font=None, **kwargs):
        super().__init__(parent, text="Model Settings", bootstyle=styles["model"]["frame"], **kwargs)

        self.speaker_identification_var = speaker_identification_var
        self.styles = styles
        

        # Label for Whisper Model
        ttk.Label(
            self,
            text="Select Whisper Model:",
            bootstyle=styles["model"]["label_model"],
            font=label_font
        ).grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))

        # Sub-frame for ComboBox
        model_frame = ttk.Frame(self)
        model_frame.grid(row=1, column=0, columnspan=5, sticky="w", padx=5, pady=2)

        # Get available VRAM
        available_vram = self._get_available_vram()

        # Prepare model compatibility labels and mappings
        self.model_options = []
        self.model_map = {}  # label -> model key
        for model_key in WHISPER_MODELS:
            base_model = WHISPER_MODELS[model_key]["default"]
            required_vram = MODEL_VRAM_REQUIREMENTS.get(base_model, 0)
            advisory = "✅ Compatible" if available_vram >= required_vram else f"⚠️ Needs {required_vram} GB"
            self.model_options.append(model_key)
            self.model_map[model_key] = {
                "base_model": WHISPER_MODELS[model_key]["default"],
                "required_vram": MODEL_VRAM_REQUIREMENTS.get(WHISPER_MODELS[model_key]["default"], 0)
            }

        # Sub-frame to group combo + advisory label horizontally
        model_frame = ttk.Frame(self)
        model_frame.grid(row=1, column=0, columnspan=5, sticky="w", padx=5, pady=2)

        # Combobox
        self.model_combobox = ttk.Combobox(
            model_frame,
            values=self.model_options,
            state="readonly",
            width=32,
            bootstyle=self.styles["model"]["dropdown_model"]
        )
        self.model_combobox.pack(side="left", padx=5)

        # Advisory label (inline)
        self.advisory_label = ttk.Label(
            model_frame,
            text="",
            bootstyle=self.styles["model"]["label_model"]
        )
        self.advisory_label.pack(side="left", padx=10)

        # Set default selection to "base"
        for idx, label in enumerate(self.model_options):
            if label.startswith("base"):
                self.model_combobox.current(idx)
                break
        else:
            self.model_combobox.current(0)  # fallback
        
        # Bind selection change + set initial advisory
        self.model_combobox.bind("<<ComboboxSelected>>", self._on_model_selected)
        self._on_model_selected()  # Trigger once on startup


        # Speaker identification checkbox
        self.checkbox = ttk.Checkbutton(
            self,
            text="Enable Speaker Identification",
            variable=self.speaker_identification_var,
            bootstyle=styles["model"]["checkbox_speaker"]
        )
        self.checkbox.grid(row=2, column=0, columnspan=5, sticky="w", padx=5, pady=(10, 5))


    def get_selected_model(self, lang_code=None):
        """Returns the resolved model name based on selected model + language code (e.g., 'tiny.en')."""
        selected_label = self.model_combobox.get()
        model_info = self.model_map.get(selected_label, {})

        base_model = model_info.get("base_model", "base")
        variants = WHISPER_MODELS.get(base_model, {})

        if lang_code == "en":
            return variants.get("en", variants.get("default", base_model))

        return variants.get("default", base_model)


    def _on_model_selected(self, event=None):
        selected_model_key = self.model_combobox.get()
        model_info = self.model_map.get(selected_model_key, {})
        base_model = model_info.get("base_model", "base")
        required_vram = model_info.get("required_vram", 0)
        available_vram = self._get_available_vram()

        advisory = "✅ GPU Compatible" if available_vram >= required_vram else f"⚠️ Needs {required_vram} GB"
        self.advisory_label.config(text=advisory)

        # Otherwise return the default model
        return WHISPER_MODELS.get(selected_model_key, {}).get("default", selected_model_key)


    def _get_available_vram(self):
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            return round(props.total_memory / (1024 ** 3), 1)
        return 0

    def set_state(self, state):
        self.model_combobox.config(state=state)
        self.checkbox.config(state=state)

    def validate(self):
        # Placeholder for future validation logic (e.g., restrict large models without GPU)
        return True
    
    