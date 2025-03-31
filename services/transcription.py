# File: transcribe_audio_service/services/transcription.py

import os
import whisper
from services.utils import get_device_status

# Internal model cache
_model_cache = {}

def get_model(model_name):
    """
    Retrieve a Whisper model from cache or load it if not already cached.
    """
    if model_name not in _model_cache:
        _model_cache[model_name] = whisper.load_model(model_name)
    return _model_cache[model_name]

def transcribe_file(file_path, model_name="medium", language="en", return_segments=False, translate_to_english=False):
    """
    Transcribes or translates a single audio file using the specified Whisper model and language.
    """

    try:
        # Step 1: Detect device
        _, cuda_available = get_device_status()
        device = "cuda" if cuda_available else "cpu"

        # Step 2: Load and move model to device
        model = get_model(model_name)
        model = model.to(device)

        # Step 3: Transcribe with optional fp16 if using GPU
        transcribe_args = {
            "language": language,
            "fp16": (device == "cuda")
            
        }

        if translate_to_english and language != "en":
            transcribe_args["task"] = "translate"

        result = model.transcribe(file_path, **transcribe_args)

        # Step 4: Format response
        response = {
            "text": result["text"]
        }

        if return_segments and "segments" in result:
            response["segments"] = result["segments"]

        return response

    except Exception as e:
        return {"error": str(e)}


def list_audio_files(directory, extensions=(".mp3", ".m4a", ".wav")):
    """
    Returns a list of audio filenames in the directory matching given extensions.
    """
    return [f for f in os.listdir(directory) if f.lower().endswith(extensions)]
