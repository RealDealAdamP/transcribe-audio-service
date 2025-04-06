# File: gui/style_config.py

import ttkbootstrap as ttk
import tkinter.font as tkfont

def get_theme_style():
    """
    Creates and returns the ttkbootstrap style + shared font config.
    """
    style = ttk.Style("cyborg")  # You could later pass this dynamically
    icon_font = tkfont.Font(size=14, weight="bold")
    label_font = tkfont.Font(size=11, weight="bold")    # For section labels
    return style, icon_font, label_font

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
            "frame": "info",
            "label_output_dir": "info",
            "entry_output_dir": "secondary",
            "button_browse": "info",
            "button_view": "info",
            "label_output_fmt": "info",
            "dropdown_output_fmt": "info",
            "check_translate": "info-round-toggle"  
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
            "button_refresh": "warning"
        },
        "controls": {
            "button_transcribe": "success",
            "button_stop": "danger",
            "label_status": "info"
        }
        
    }
