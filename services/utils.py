import os
import json
import csv
import datetime
from mutagen import File as MutagenFile
from copy import deepcopy
from xml.etree.ElementTree import ElementTree
import re
from services.constants import LANGUAGE_MAP, BATCH_SIZE_THRESHOLDS
import torch

def _expand_key(compact_key):
    """
    Converts template keys like 'AudioFileName' to 'Audio File Name'
    to match metadata dictionary keys.
    """
    return " ".join([w for w in re.findall(r'[A-Z][a-z]*', compact_key)])

def get_lang_name(code):
    for name, lang_code in LANGUAGE_MAP.items():
        if lang_code == code:
            return name
    return code  # fallback to code if no match found

def get_transcription_metadata(file_path, input_language, output_language, model_used, processing_device=None,batch_size=8):
    """Returns categorized metadata for the transcription process."""

    # Get basic file properties
    input_section = {
        "Audio File Name": os.path.basename(file_path),
        "Audio File Creation Date": datetime.datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%Y-%m-%d %H:%M:%S"),
        "Audio Language": input_language,
        "Audio File Item Type": os.path.splitext(file_path)[1][1:]  # e.g., 'mp3', 'wav'
        
    }

    # File size
    try:
        size_bytes = os.path.getsize(file_path)
        input_section["Audio File Size"] = f"{round(size_bytes / (1024 * 1024), 2)} MB"
    except Exception:
        input_section["Audio File Size"] = "Unknown"

    # Audio properties via mutagen
    try:
        audio = MutagenFile(file_path)
        if audio is not None and hasattr(audio, "info"):
            duration_sec = getattr(audio.info, "length", None)
            bitrate = getattr(audio.info, "bitrate", None)

            if duration_sec is not None:
                minutes, seconds = divmod(int(duration_sec), 60)
                input_section["Audio File Length"] = f"{minutes:02}:{seconds:02} ({round(duration_sec, 2)} sec)"
            else:
                input_section["Audio File Length"] = "Unknown"

            if bitrate is not None:
                input_section["Audio Bit Rate"] = f"{round(bitrate / 1000, 2)} kbps"
            else:
                input_section["Audio Bit Rate"] = "Unknown"
        else:
            input_section["Audio File Length"] = "Unknown"
            input_section["Audio Bit Rate"] = "Unknown"

    except Exception:
        input_section["Audio File Length"] = "Error"
        input_section["Audio Bit Rate"] = "Error"

    return {
        "Input": input_section,
        "Output": {
            "Transcription Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Whisper Model": model_used,
            "Whisper Processing Device": processing_device or "Unknown",
            "Whisper Batch Size": batch_size,
            "Output Text Language": output_language
        }
    }

def save_transcript(output_path, text, template, input_file=None, input_language="en", output_language="en",model_used=None,processing_device=None,batch_size=8, output_format="txt"):
    """
    Save the transcription output to various formats using the provided template.

    Parameters:
        output_path (str): Full path including filename and extension.
        text (str): The transcription text.
        template (object): Preloaded template object (dict, string, list, or ElementTree root).
        input_file (str): Path to the original audio file (for metadata).
        input_language (str): Language code of the original audio.
        output_language (str): Language code of the output transcript.
        output_format (str): One of 'txt', 'json', 'csv', 'xml'.
    """
    metadata = get_transcription_metadata(input_file, input_language, output_language, model_used, processing_device, batch_size) if input_file else {}

    # Flatten nested metadata for string-based templates like .txt
    flat_metadata = {
        **metadata.get("Input", {}),
        **metadata.get("Output", {})
    }

    # Merge flat metadata with transcription text
    merged_data = {**flat_metadata, "Transcription Text": text}

    if output_format == "txt":
        # Template is a string with placeholders
        rendered = template.format(**merged_data)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)

    elif output_format == "json":
        json_data = deepcopy(template)
        json_data["Input"] = metadata.get("Input", {})
        json_data["Output"] = metadata.get("Output", {})
        json_data["Transcription Text"] = text

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

    elif output_format == "csv":
       # Template headers like ['AudioFileName', 'AudioFileCreationDate', ...]
        rows = [(field, text if field == "Transcription Text" else flat_metadata.get(_expand_key(field), ""))
    for field in template
]
        with open(output_path, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Field", "Value"])
            writer.writerows(rows)

    elif output_format == "xml":
        root = deepcopy(template)
        
        for child in root:
            tag = child.tag

            if tag == "Input":
                for sub in child:
                    value = metadata.get("Input", {}).get(_expand_key(sub.tag))
                    if value is not None:
                        sub.text = str(value) 

            elif tag == "Output":
                for sub in child:
                    value = metadata.get("Output", {}).get(_expand_key(sub.tag))
                    if value is not None:
                        sub.text = str(value) 

            elif tag == "TranscriptionText":
                child.text = text

        tree = ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def get_device_status():
    """Returns a tuple (device_str, cuda_available_bool)."""
    if torch.cuda.is_available():
        device = torch.cuda.get_device_name(0)
        return (device, True)
    return ("CPU", False)

def get_optimal_batch_size(vram_gb, using_gpu):
    if not using_gpu:
        return BATCH_SIZE_THRESHOLDS["low"]["batch_size"]

    if vram_gb >= BATCH_SIZE_THRESHOLDS["high"]["vram"]:
        return BATCH_SIZE_THRESHOLDS["high"]["batch_size"]
    elif vram_gb >= BATCH_SIZE_THRESHOLDS["medium"]["vram"]:
        return BATCH_SIZE_THRESHOLDS["medium"]["batch_size"]
    else:
        return BATCH_SIZE_THRESHOLDS["low"]["batch_size"]
    
def qualifies_for_batch_processing(file_path, use_diarization):
    try:
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        return use_diarization or size_mb > 25
    except Exception:
        return False  # Fail safe: assume no