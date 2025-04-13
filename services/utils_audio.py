# File: transcribe_audio_service/services/utils_audio.py

import subprocess
import tempfile
import os
from cfg.conf_main import SUPPORTED_AUDIO_EXTENSIONS


def prep_whisper_audio(path, temp_dir, target_sr=16000, bitrate="32k"):
    """
    Convert audio to high-fidelity MP3 format for Whisper using FFmpeg.

    Returns:
        str: Path to the newly converted MP3 file.
    """
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir=temp_dir) as tmp:
        compressed_mp3_path = tmp.name

    command = [
        "ffmpeg", "-i", path,
        "-ac", "1",                    # mono
        "-ar", str(target_sr),        # 16 kHz
        "-b:a", bitrate,              # 32 kbps
        "-f", "mp3",
        compressed_mp3_path,
        "-y"
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return compressed_mp3_path


def list_audio_files(directory, extensions=SUPPORTED_AUDIO_EXTENSIONS):
    """
    Returns a list of audio filenames in the directory matching supported extensions.
    """
    return [f for f in os.listdir(directory) if f.lower().endswith(extensions)]

def tmp_audio_cleanup(file_path):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Warning: Failed to delete temp file {file_path}: {e}")