# File: transcribe_audio_service/services/dependency_check.py

import shutil
from tkinter import messagebox

def check_ffmpeg():
    """Check if ffmpeg is available in system PATH."""
    if not shutil.which("ffmpeg"):
        messagebox.showerror(
            title="Missing Dependency",
            message=(
                "FFmpeg is not installed or not added to your system PATH.\n\n"
                "Please install FFmpeg and make sure it's accessible via command line.\n"
                "Download: https://ffmpeg.org/download.html"
            )
        )
        return False
    return True


def check_dependencies():
    """Run all startup dependency checks. Return True if all pass."""
    return check_ffmpeg()  