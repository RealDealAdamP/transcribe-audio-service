# File: transcribe_audio_service/gui/app.py

import ttkbootstrap as ttk
from gui.ui_main import TranscribeApp


def launch_app():
    root = ttk.Window(themename="darkly")
    app = TranscribeApp(root)
    root.mainloop()
