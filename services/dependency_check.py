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

def check_pyannote_model():
    """Ensure PyAnnote diarization model is cached locally."""
    from pyannote.audio import Pipeline
    from huggingface_hub.utils import RepositoryNotFoundError, RevisionNotFoundError
    import os

    try:
        Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=os.getenv("HUGGINGFACE_TOKEN"),
            cache_dir=".models/pyannote"
        )
        return True
    except (RepositoryNotFoundError, RevisionNotFoundError) as e:
        messagebox.showerror(
            title="Missing PyAnnote Model",
            message=(
                "The PyAnnote speaker diarization model could not be loaded.\n\n"
                "Please verify your Hugging Face token is set as an environment variable:\n"
                "HUGGINGFACE_TOKEN=your_token_here\n\n"
                "Also ensure you have permission to access the model:\n"
                "https://huggingface.co/pyannote/speaker-diarization-3.1"
            )
        )
        return False
    except Exception as e:
        messagebox.showerror(
            title="PyAnnote Error",
            message=f"Unexpected error loading diarization model:\n\n{str(e)}"
        )
        return False

def check_dependencies():
    """Run all startup dependency checks. Return True if all pass."""
    return check_ffmpeg()  and check_pyannote_model()
