# File: transcribe_audio_service/gui/app.py

import ttkbootstrap as ttk
from gui.layout import TranscribeAudioService

def launch_app():
    root = ttk.Window(themename="darkly")
    app = TranscribeAudioService(root)
    root.mainloop()
