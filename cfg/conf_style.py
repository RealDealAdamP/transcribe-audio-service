# File: cfg/conf_style.py

import ttkbootstrap as ttk
import tkinter.font as tkfont

def get_theme_style():
    style = ttk.Style("cyborg")

    # Icon fonts
    icon_font = ("Segoe UI Emoji", 18, "bold")
    bg = "#060606"

    # Safe, compound style names
    style.configure("IconSuccess.TButton", font=icon_font, foreground="#77b303", background=bg)
    style.configure("IconInfo.TButton", font=icon_font, foreground="#9933cc", background=bg)
    style.configure("IconWarning.TButton", font=icon_font, foreground="#ff8803", background=bg)
    style.configure("IconDanger.TButton", font=icon_font, foreground="red", background=bg)
    style.configure("IconPrimary.TButton", font=icon_font, foreground="#2A9FD6", background=bg)

    fonts = {
        "label": tkfont.Font(size=11, weight="bold"),
        "icon": tkfont.Font(family="Segoe UI Emoji", size=18, weight="bold")
    }

    return style, fonts


def get_bootstyles():
    """
Returns a dictionary of ttkbootstrap bootstyle tokens grouped by UI frame.
This centralized style map ensures consistent styling across all GUI modules 
and simplifies maintenance and theming for the application.
    
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


        "splash": {
            "frame": "dark",
            "label_title": "primary",
            "label_status": "success",
            "label_footer": "warning",  # ← NEW: subtle gray/neutral style
            "progressbar": "warning-striped"
        },
        
        "input": {
            "frame": "success",
            "label_input_dir": "success",
            "entry_input_dir": "secondary",
            "button_browse": "success",
            "button_view" : 'success',
            "label_lang": "success",
            "dropdown_lang": "success",
            "label_monitoring": "success",          
            "checkbox_monitoring": "success-round-toggle",  
            "label_interval": "success",            
            "scale_interval": "success"              
        },
        "output": {
            "frame": "primary",
            "label_output_dir": "primary",
            "entry_output_dir": "secondary",
            "button_browse": "primary",
            "button_view": "primary",
            "label_output_fmt": "primary",
            "dropdown_output_fmt": "primary",
            "check_translate": "primary-round-toggle"  
        },
        "model": {
            "frame": "warning",
            "label_model": "warning",
            "dropdown_model": "warning",             # renamed from combobox_model
            "checkbox_speaker": "warning-round-toggle"
        },
        
        "monitor": {
            "frame": "warning",
            "low": "warning",
            "high": "danger",
            "inactive":"secondary"
        },
        "queue": {
            "frame": "warning",  # Optional if you wrap QueueFrame in a LabelFrame someday
            "label_queue": "warning",
            "label_status": "warning",
            "label_output_txt": "warning",
            "entry_search":"warning",
            "button_refresh": "warning",
            "label_cluster" : "warning"

        },
        "controls": {
            "button_transcribe": "success",
            "button_stop": "danger",
            "label_status": "info"
        }
        
    }
