# File: transcribe_audio_service/services/utils_transcribe.py
import os
from services.utils_models import get_whisper_model
import datetime
from tinytag import TinyTag
from cfg.conf_main import LANGUAGE_MAP
from services.utils_output import SAVE_OUTPUT_FUNCTIONS
import pandas as pd
import re

def transcribe_file(
    audio_mp3_path,
    model_name="medium",
    language="en",
    translate_to_english=False,
):
    """
    Prepares audio and runs Whisper transcription.

    Returns:
        dict: Whisper result with "text" and optional "segments"
    """
    model, device = get_whisper_model(model_name)

    return run_whisper_transcription(
        audio_mp3_path=audio_mp3_path,
        model=model,
        device=device,
        language=language,
        translate_to_english=translate_to_english
    )


def run_whisper_transcription(
    audio_mp3_path,
    model,
    device,
    language="en",
    translate_to_english=False,
):
    """
    Runs Whisper transcription on a prepared MP3 file.
    """
    try:
        transcribe_args = {
            "language": language,
            "fp16": (device == "cuda")
        }

        if translate_to_english and language != "en":
            transcribe_args["task"] = "translate"

        result = model.transcribe(audio_mp3_path, **transcribe_args)
        print(audio_mp3_path)

        return result

    except Exception as e:
        print(f"❌ Whisper failed with error: {e}")
        return {"error": str(e)}
    



def save_transcript(
    output_path,
    result,
    template,
    input_file=None,
    input_language="en",
    output_language="en",
    model_used=None,
    processing_device=None,
    batch_size=8,
    use_diarization=False,
    output_format="txt",
):
    # Get metadata
    if input_file:
        metadata = get_transcription_metadata(
            input_file, input_language, output_language,
            model_used, processing_device, batch_size
        )
    else:
        metadata = {}

    flat_metadata = {
        **metadata.get("Input", {}),
        **metadata.get("Output", {})
    }

    pd.DataFrame(result).to_csv(r"C:\demo\save_trans_input.csv", index=False, float_format="%.8f")
    #

    # Extract raw transcription  text
    raw_text = result.get("text", "")
    segments = result.get("segments", [])
    
    # Initialize df based on whether diarization is enabled
    if use_diarization:
        df = apply_diarize_time({"segments": segments, "text": raw_text})
    else:
        df = pd.DataFrame(segments) if segments else None
    
    # Apply speaker labels to raw text
    if use_diarization and df is not None:
        diarized_lines = []
        for _, row in df.iterrows():
            speaker_id = row.get("speaker", "Unknown")
            speaker_label = f"[Speaker {speaker_id}]"
            line = f"{speaker_label} {row['text'].strip()}"
            diarized_lines.append(line)
        raw_text = "\n".join(diarized_lines)

    # Step 3: Final merge
    merged_data = {
        "Input": metadata.get("Input", {}),
        "Output": metadata.get("Output", {}),
        "Transcription Text": raw_text,
        "Flat": flat_metadata,
        "Raw Text": raw_text,
        "Template": template,
        "DataFrame": df  # only used by srt/vtt
    }
    

    # Dispatch to correct format
    output_format = output_format.lower()
    if output_format in SAVE_OUTPUT_FUNCTIONS:
        SAVE_OUTPUT_FUNCTIONS[output_format](output_path, merged_data)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def get_transcription_metadata(file_path, input_language, output_language, model_used, processing_device=None, batch_size=8):
    """Returns categorized metadata for the transcription process."""

    # Get basic file properties
    input_section = {
        "Audio File Name": os.path.basename(file_path),
        "Audio File Creation Date": datetime.datetime.fromtimestamp(os.path.getctime(file_path)),
        "Audio Language": input_language,
        "Audio File Item Type": os.path.splitext(file_path)[1][1:]  # e.g., 'mp3', 'wav'
    }

    # File size
    try:
        size_bytes = os.path.getsize(file_path)
        input_section["Audio File Size"] = f"{round(size_bytes / (1024 * 1024), 2)} MB"
    except Exception:
        input_section["Audio File Size"] = "Unknown"

    # Audio properties via tinytag
    try:
        tag = TinyTag.get(file_path)
        duration_sec = tag.duration
        bitrate = tag.bitrate

        input_section["Audio File Length"] = (
            f"{int(duration_sec // 60):02}:{int(duration_sec % 60):02} ({round(duration_sec, 2)} sec)"
            if duration_sec is not None else "Unknown"
        )
        input_section["Audio Bit Rate"] = (
            f"{round(bitrate, 2)} kbps" if bitrate is not None else "Unknown"
        )
    except Exception:
        input_section["Audio File Length"] = "Error"
        input_section["Audio Bit Rate"] = "Error"

    metadata = {
        "Input": input_section,
        "Output": {
            "Transcription Date": datetime.datetime.now(),
            "Whisper Model": model_used,
            "Whisper Processing Device": processing_device or "Unknown",
            "Whisper Batch Size": batch_size,
            "Output Text Language": output_language
        }
    }

    return metadata


    
def qualifies_for_batch_processing(file_path, use_diarization):
    try:
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        return use_diarization or size_mb > 25
    except Exception:
        return False  # Fail safe: assume no
    

def apply_diarize_time(result):

    """New time format Required for SRT / VTT compatability 
    for now we apply the same irrespective of output format"""

    segments = result.get("segments", [])
    diarize_labels = []
    for seg in segments:
        start_time = format_time(seg["start"])
        end_time = format_time(seg["end"])
        diarize_labels.append({
            "id": seg["id"],
            "start": seg["start"],
            "end": seg["end"],
            "start_time": start_time,
            "end_time": end_time,
            "speaker": seg["speaker"],
            "text": seg["text"]
        })

    return pd.DataFrame(diarize_labels)

def format_time(seconds):
    """Convert float seconds to SRT time format (HH:MM:SS,mmm)."""
    ms = int((seconds - int(seconds)) * 1000)
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def get_lang_name(code):
    for name, lang_code in LANGUAGE_MAP.items():
        if lang_code == code:
            return name
    return code  # fallback to code if no match found


