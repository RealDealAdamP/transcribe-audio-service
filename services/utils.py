import os
import json
import csv
import datetime
from copy import deepcopy
from xml.etree.ElementTree import ElementTree
import re
from services.constants import LANGUAGE_MAP

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

def get_transcription_metadata(file_path, input_language, output_language):
    """Returns categorized metadata for the transcription process."""
    return {
        "Input": {
            "Audio File Name": os.path.basename(file_path),
            "Audio File Creation Date": datetime.datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%Y-%m-%d %H:%M:%S"),
            "Audio File Length": "Unknown",  # Placeholder
            "Audio File Item Type": os.path.splitext(file_path)[1][1:],  # 'mp3', 'wav'
            "Audio Language": input_language
        },
        "Output": {
            "Transcription Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Output Text Language": output_language
        }
    }

def save_transcript(output_path, text, template, input_file=None, input_language="en", output_language="en", output_format="txt"):
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
    metadata = get_transcription_metadata(input_file, input_language, output_language) if input_file else {}

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
            json.dump(json_data, f, indent=2)

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
                    if value:
                        sub.text = value

            elif tag == "Output":
                for sub in child:
                    value = metadata.get("Output", {}).get(_expand_key(sub.tag))
                    if value:
                        sub.text = value

            elif tag == "TranscriptionText":
                child.text = text

        tree = ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

    else:
        raise ValueError(f"Unsupported output format: {output_format}")

