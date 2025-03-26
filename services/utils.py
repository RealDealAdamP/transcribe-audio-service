import os
import json
import csv
import datetime
from copy import deepcopy
from xml.etree.ElementTree import ElementTree
import re

def _expand_key(compact_key):
    """
    Converts template keys like 'AudioFileName' to 'Audio File Name'
    to match metadata dictionary keys.
    """
    return " ".join([w for w in re.findall(r'[A-Z][a-z]*', compact_key)])


def get_audio_metadata(file_path):
    """Mocked metadata logic — replace with actual duration, file type, etc."""
    return {
        "Audio File Name": os.path.basename(file_path),
        "Audio File Creation Date": datetime.datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%Y-%m-%d %H:%M:%S"),
        "Audio File Length": "Unknown",  # Placeholder — use librosa or pydub later
        "Audio File Item Type": os.path.splitext(file_path)[1][1:],  # 'mp3', 'wav'
        "Transcription Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def save_transcript(output_path, text, template, input_file=None, output_format="txt"):
    """
    Save the transcription output to various formats using the provided template.

    Parameters:
        output_path (str): Full path including filename and extension.
        text (str): The transcription text.
        template (object): Preloaded template object (dict, string, list, or ElementTree root).
        input_file (str): Path to the original audio file (for metadata).
        output_format (str): One of 'txt', 'json', 'csv', 'xml'.
    """
    metadata = get_audio_metadata(input_file) if input_file else {}
    merged_data = {**metadata, "Transcription Text": text}

    if output_format == "txt":
        # Template is a string with placeholders
        rendered = template.format(**merged_data)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)

    elif output_format == "json":
        json_data = deepcopy(template)
        for key in json_data:
            if key in merged_data:
                json_data[key] = merged_data[key]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

    elif output_format == "csv":
       # Template headers like ['AudioFileName', 'AudioFileCreationDate', ...]
        rows = [(field, merged_data.get(_expand_key(field), "")) for field in template]
        with open(output_path, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Field", "Value"])
            writer.writerows(rows)

    elif output_format == "xml":
        root = deepcopy(template)
        for child in root:
            tag = child.tag
            value = merged_data.get(_expand_key(tag))
            if value:
                child.text = value
        tree = ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

    else:
        raise ValueError(f"Unsupported output format: {output_format}")

