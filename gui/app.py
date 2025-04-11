# File: transcribe_audio_service/gui/app.py

from gui.ui_main import TranscribeApp

def launch_app(root):
    """
    Launches the main Transcribe UI using the provided root window.
    Assumes splash screen logic has already been handled.
    """
    app = TranscribeApp(root)
    return app  # Optionally return the app instance if needed
