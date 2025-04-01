# File: transcribe_audio_service/services/transcription.py

import os
import whisper
from services.utils_transcribe import get_device_status
from services.utils_audio import prep_whisper_audio, prep_pyannote_audio
from pyannote.audio import Pipeline
from services.constants import SUPPORTED_AUDIO_EXTENSIONS
import torch


import tempfile
import soundfile as sf

# Internal model cache
_model_cache = {}
#Internal pipeline cache for pyannote diarization
_pyannote_pipeline = None  

def get_model(model_name):
    """
    Retrieve a Whisper model from cache or load it if not already cached.
    """
    if model_name not in _model_cache:
        _model_cache[model_name] = whisper.load_model(model_name)
    return _model_cache[model_name]

def get_pyannote_pipeline():
    global _pyannote_pipeline
    if _pyannote_pipeline is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        CACHE_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", ".models", "pyannote"))

        token = os.getenv("HUGGINGFACE_TOKEN")
        load_args = {"cache_dir": CACHE_DIR}
        if token:
            load_args["use_auth_token"] = token

        _pyannote_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", **load_args)

        # Send to GPU if available
        if torch.cuda.is_available():
            _pyannote_pipeline.to(torch.device("cuda"))

    return _pyannote_pipeline


def transcribe_file(
    audio_path,
    temp_dir=None,
    model_name="medium",
    language="en",
    return_segments=False,
    translate_to_english=False,
):
    """
    Transcribes or translates an audio file using the specified Whisper model and language.

    Parameters:
        audio_path (str): Path to original audio file (any format supported by ffmpeg).
        model_name (str): Whisper model name (e.g., "base", "medium", "large").
        language (str): Language code of the spoken language.
        return_segments (bool): Whether to return segment-level results.
        translate_to_english (bool): If True, translates non-English to English.

    Returns:
        dict: Transcription result with "text" key (and optionally "segments").
    """
    model, device = get_whisper_model(model_name)

    return run_whisper_transcription(
        audio_path=audio_path,
        temp_dir=temp_dir,
        model=model,
        device=device,
        language=language,
        translate_to_english=translate_to_english,
        return_segments=return_segments
    )


def transcribe_file_with_diarization(
    audio_path: str,
    temp_dir,
    model_name: str = "medium",
    language: str = "en",
    translate_to_english: bool = False
) -> dict:
    """
    Performs speaker diarization + transcription using a preloaded waveform.
    Returns a speaker-labeled transcript in the same format as transcribe_file().
    """
    try:
        
        # Step 1: Load waveform and sample rate from file
        waveform, sample_rate = prep_pyannote_audio(audio_path, temp_dir)

        # Step 2: Load PyAnnote pipeline
        pipeline = get_pyannote_pipeline()
        diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate})

        # Step 3: Load Whisper model
        model, device = get_whisper_model(model_name)
        speaker_transcripts = []

        # Step 4: Slice waveform and transcribe each segment
        for segment, _, speaker in diarization.itertracks(yield_label=True):
            start_sample = int(segment.start * sample_rate)
            end_sample = int(segment.end * sample_rate)
            segment_waveform = waveform[0][start_sample:end_sample]  # waveform is [1, N]

            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir=temp_dir) as tmp:
                    temp_segment_wav_path = tmp.name

                sf.write(temp_segment_wav_path, segment_waveform.numpy(), sample_rate)

                result = run_whisper_transcription(
                    audio_path=temp_segment_wav_path,
                    temp_dir=temp_dir,
                    model=model,
                    device=device,
                    language=language,
                    translate_to_english=translate_to_english,
                    return_segments=False
                )

                # Format transcript entry
                start = format_timestamp(segment.start)
                end = format_timestamp(segment.end)
                text = result.get("text", "[Transcription Error]").strip()
                speaker_transcripts.append(f"[{start} - {end}] {speaker}: {text}")

            finally:
                if os.path.exists(temp_segment_wav_path):
                    os.remove(temp_segment_wav_path)

        return {"text": "\n".join(speaker_transcripts)}

    except Exception as e:
        return {"error": str(e)}


def format_timestamp(seconds: float) -> str:
    """
    Formats float seconds into HH:MM:SS.mmm timestamp.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:06.3f}"


def list_audio_files(directory, extensions=SUPPORTED_AUDIO_EXTENSIONS):
    """
    Returns a list of audio filenames in the directory matching supported extensions.
    """
    return [f for f in os.listdir(directory) if f.lower().endswith(extensions)]


def get_whisper_model(model_name="medium"):
    """
    Loads and returns a Whisper model on the appropriate device.
    """
    _, cuda_available = get_device_status()
    device = "cuda" if cuda_available else "cpu"

    model = get_model(model_name)
    return model.to(device), device

def run_whisper_transcription(
    audio_path,
    temp_dir,
    model,
    device,
    language="en",
    translate_to_english=False,
    return_segments=False
):
    """
    Runs Whisper transcription on an optimized MP3 audio file.

    Parameters:
        audio_path (str): Path to original audio file.
        model: Loaded Whisper model.
        device: Target device ("cuda" or "cpu").
        language (str): Language code (e.g. "en").
        translate_to_english (bool): If True, perform translation to English.
        return_segments (bool): If True, return segment-level data.

    Returns:
        dict: {"text": ..., "segments": ...}
    """
    try:
        # Convert input audio to compressed MP3 (12kHz, mono, 16kbps)
        audio_mp3_path = prep_whisper_audio(audio_path,temp_dir)

        transcribe_args = {
            "language": language,
            "fp16": (device == "cuda")
        }

        if translate_to_english and language != "en":
            transcribe_args["task"] = "translate"

        result = model.transcribe(audio_mp3_path, **transcribe_args)

        response = {"text": result["text"]}
        if return_segments and "segments" in result:
            response["segments"] = result["segments"]

        return response

    except Exception as e:
        print(f"❌ Whisper failed with error: {e}")
        return {"error": str(e)}