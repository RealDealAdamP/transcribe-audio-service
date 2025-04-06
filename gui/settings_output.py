# File: gui/settings_output.py

import tkinter as tk
import ttkbootstrap as ttk
from services.constants import SUPPORTED_OUTPUT_EXTENSIONS

class SettingsOutputFrame(ttk.LabelFrame):
    def __init__(
        self,
        parent,
        output_dir_var,
        output_format_var,
        translate_var, 
        language_var,
        styles,
        label_font=None,
        on_format_change=None,
        browse_callback=None,
        view_callback=None,
        **kwargs
    ):
        super().__init__(parent, text="Output Settings", bootstyle=styles["output"]["frame"], **kwargs)

        self.output_dir_var = output_dir_var
        self.output_format_var = output_format_var
        self.translate_var = translate_var
        self.language_var = language_var
        self.on_format_change = on_format_change
        self.styles = styles
        self.browse_callback = browse_callback 
        self.view_callback = view_callback 
        
        # Output Directory Label
        ttk.Label(
            self,
            text="Output Directory:",
            bootstyle=styles["output"]["label_output_dir"],
            font=label_font
        ).grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))

        # Output Directory Entry
        entry_output = ttk.Entry(self, 
                                 textvariable=self.output_dir_var, 
                                 width=50, state="readonly",
                                 bootstyle=styles["output"]["entry_output_dir"])
        
        entry_output.grid(row=1, column=0, padx=(5, 2), pady=5, sticky="ew")

        # 🧱 Sub-frame for Browse + View buttons
        button_group = ttk.Frame(self)
        button_group.grid(row=1, column=1, padx=(2, 5), pady=5, sticky="w")

        # Browse Button
        ttk.Button(
            button_group,
            text="Browse",
            command=browse_callback,
            bootstyle=styles["output"]["button_browse"]
        ).grid(row=0, column=0, padx=(0, 4))

        # View Button (icon only)
        ttk.Button(
            button_group,
            text="📂",
            width=3,
            command=view_callback,
            bootstyle=styles["output"]["button_view"]
        ).grid(row=0, column=1)

        # Output Format Label
        ttk.Label(
            self,
            text="Select Output Format:",
            bootstyle=styles["output"]["label_output_fmt"],
            font=label_font
        ).grid(row=2, column=0, sticky="w", padx=5, pady=(10, 2))

        # Output Format Dropdown
        self.format_dropdown = ttk.Combobox(
            self,
            textvariable=self.output_format_var,
            values=list(SUPPORTED_OUTPUT_EXTENSIONS),
            state="readonly",
            bootstyle=styles["output"]["dropdown_output_fmt"]
        )
        self.format_dropdown.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.format_dropdown.bind("<<ComboboxSelected>>", self.handle_format_change)
        

        # Row 3 – Spacer
        ttk.Label(self, text="").grid(row=4, column=0, pady=(5, 0))

        #Translate Output 
        self.translate_checkbox = ttk.Checkbutton(
            self,
            text="Translate → English",
            variable=self.translate_var,
            bootstyle=styles["output"]["check_translate"]
        )
        self.translate_checkbox.grid(row=5, column=0, padx=5, pady=(0, 5), sticky="w")

        self.update_translate_state()
    
    def handle_format_change(self, event=None):
        if self.on_format_change:
            self.on_format_change()

    def set_state(self, state):
        for child in self.winfo_children():
            try:
                child.configure(state=state)
            except tk.TclError:
                pass

    def validate(self):
        if not self.output_dir_var.get():
            tk.messagebox.showerror("Validation Error", "Please select an output directory.")
            return False
        if not self.output_format_var.get():
            tk.messagebox.showerror("Validation Error", "Please select an output format.")
            return False
        return True

    def update_translate_state(self):
            selected_lang_code = self.language_var.get()
            if selected_lang_code == "en":
                self.translate_checkbox.state(["disabled"])
                self.translate_var.set(False)
            else:
                self.translate_checkbox.state(["!disabled"])

    def set_format_options(self, format_list):
        self.format_dropdown.config(values=format_list)

        # Optional: reset selected value if it's now invalid
        current_value = self.output_format_var.get()
        if current_value not in format_list:
            self.output_format_var.set(format_list[0])