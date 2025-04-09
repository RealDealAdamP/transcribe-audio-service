# File: transcribe_audio_service/services/utils_models.py
import whisper
import re
from services.utils_device import get_device_status
import pandas as pd

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

def find_new_seg_id(segments, punctuation_merge=True):
    """
    Assigns a new segment ID to each Whisper segment by grouping adjacent
    fragments based on punctuation criteria, while retaining all original
    segment metadata.

    Parameters:
        segments (list): List of Whisper segment dicts (each must include 'start', 'end', and 'text')
        punctuation_merge (bool): If True, only merge with prior segment if it lacks terminal punctuation.

    Returns:
        List of segment dicts with an additional field: 'new_segment_id'.
    """
    updated_segments = []
    seg_id = 1
    current_group = []

    for seg in segments:
        text = seg["text"].strip()

        if not current_group:
            current_group.append(seg)
            continue

        prev_text = current_group[-1]["text"].strip()
        ends_with_punct = bool(re.search(r"[.?!…]$", prev_text))

        if punctuation_merge and ends_with_punct:
            for s in current_group:
                updated_segments.append({**s, "new_segment_id": seg_id})
            seg_id += 1
            current_group = [seg]
        else:
            current_group.append(seg)

    if current_group:
        for s in current_group:
            updated_segments.append({**s, "new_segment_id": seg_id})

    return updated_segments


