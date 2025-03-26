# File: gui/style_config.py

import ttkbootstrap as ttk
import tkinter.font as tkfont

def get_theme_style():
    """
    Creates and returns the ttkbootstrap style + shared font config.
    """
    style = ttk.Style("solar")  # You could later pass this dynamically
    icon_font = tkfont.Font(size=12, weight="bold")
    return style, icon_font

def get_bootstyles():
    """
    Returns a dictionary mapping semantic UI elements to ttkbootstrap bootstyle tokens.
    Designed to unify styling across all GUI modules.
    
primary:The default color for most widgets
secondary:Typically a gray color
success:Typically a green color	
info:Typically a blue color
warning:typically an orange color	
danger:Typically a red color	
light:Typically a light gray color	
dark:Typically a dark gray color	
    
    """
    return {
        # Section labels
        "label_directory": "info",
        "label_settings": "success",
        "label_model": "info",
        "label_lang": "info",
        "label_output": "info",
        "label_options": "info",
        "label_queue": "info",
        "label_status": "info",
        "label_output_txt": "info",

        # Buttons
        "button_browse": "primary",
        "button_refresh": "secondary",
        "button_transcribe": "primary",
        "button_stop": "danger",

        # Radio buttons
        "model_radio": "info",
        "lang_radio": "info",
        "output_radio": "info",

        # Checkbutton or Switch
        "speaker_toggle": "danger"
    }
