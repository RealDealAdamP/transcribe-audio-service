# File: transcribe_audio_service/services/utils_models.py
import whisper
import re
from services.utils_device import get_device_status

# Internal model cache
_model_cache = {}

def get_model(model_name):
    """
    Retrieve a Whisper model from cache or load it if not already cached.
    """
    if model_name not in _model_cache:
        _model_cache[model_name] = whisper.load_model(model_name)
    return _model_cache[model_name]

def get_whisper_model(model_name="medium"):
    """
    Loads and returns a Whisper model on the appropriate device.
    """
    _, cuda_available = get_device_status()
    device = "cuda" if cuda_available else "cpu"

    model = get_model(model_name)
    return model.to(device), device

def merge_whisper_segments(segments, punctuation_merge=True):
    """
    Merge fragmented Whisper segments and update timestamps accordingly.

    Parameters:
    - segments (list): List of Whisper-style segment dicts
    - punctuation_merge (bool): If True, only merge if previous segment lacks terminal punctuation.

    Returns:
    - List of merged segment dicts with updated start/end and merged text.
    """
    merged_segments = []
    current = None

    for seg in segments:
        text = seg["text"].strip()

        if current is None:
            current = seg.copy()
            continue

        should_merge = False

        if punctuation_merge:
            should_merge = not re.search(r"[.?!…]$", current["text"].strip())
        else:
            should_merge = True

        if should_merge:
            # Merge current and seg
            current["text"] = current["text"].rstrip() + " " + text
            current["end"] = seg["end"]
        else:
            # Push current and start new
            merged_segments.append(current)
            current = seg.copy()

    if current:
        merged_segments.append(current)

    return merged_segments


