# File: transcribe_audio_service/services/transcription.py

import os
import whisper

# Internal model cache
_model_cache = {}

def get_model(model_name):
    """
    Retrieve a Whisper model from cache or load it if not already cached.
    """
    if model_name not in _model_cache:
        _model_cache[model_name] = whisper.load_model(model_name)
    return _model_cache[model_name]

def transcribe_file(file_path, model_name="medium", language="en", return_segments=False):
    """
    Transcribes a single audio file using the specified Whisper model and language.

    Parameters:
        file_path (str): Path to the audio file.
        model_name (str): Whisper model name ("base", "small", "medium", "large").
        language (str): Language code (e.g., "en", "es").
        return_segments (bool): If True, include segment-level results (for diarization).

    Returns:
        dict: Contains at least 'text'. May include 'segments' if requested.
    """
    try:
        model = get_model(model_name)
        result = model.transcribe(file_path, language=language)

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
