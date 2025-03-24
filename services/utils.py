# File: transcribe_audio_service/services/utils.py

import os

def transcription_exists(audio_file_path):
    """Check if the corresponding .txt transcript already exists."""
    base, _ = os.path.splitext(audio_file_path)
    return os.path.exists(f"{base}.txt")

def save_transcript(output_path, text):
    """Save transcription text to a .txt file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)