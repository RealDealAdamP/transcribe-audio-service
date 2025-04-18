# File: transcribe_audio_service/services/utils_output.py
import json
import csv
import pandas as pd
from copy import deepcopy
from xml.etree.ElementTree import ElementTree
import datetime
import re
import os 
from pathlib import Path

# ────────────────────────────────────────────────
# Core Methods
# ────────────────────────────────────────────────

def save_as_txt(path, data):
    rendered = data["Template"].format(**data["Flat"], **{"Transcription Text": data["Raw Text"]})
    with open(path, "w", encoding="utf-8") as f:
        f.write(rendered)

def save_as_json(path, data):
    obj = deepcopy(data["Template"])
    obj["Input"] = data["Input"]
    obj["Output"] = data["Output"]
    obj["Transcription Text"] = data["Raw Text"]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def save_as_csv(path, data):
    flat = data["Flat"]
    template = data["Template"]
    text = data["Raw Text"]

    row_values = [
        text if field == "Transcription Text" else flat.get(_expand_key(field), "")
        for field in template
    ]

    with open(path, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(template)
        writer.writerow(row_values)

def save_as_xml(path, data):
    template = deepcopy(data["Template"])
    for child in template:
        tag = child.tag
        if tag == "Input":
            for sub in child:
                value = data["Input"].get(_expand_key(sub.tag))
                if value is not None:
                    sub.text = str(value)
        elif tag == "Output":
            for sub in child:
                value = data["Output"].get(_expand_key(sub.tag))
                if value is not None:
                    sub.text = str(value)
        elif tag == "TranscriptionText":
            child.text = data["Raw Text"]

    ElementTree(template).write(path, encoding="utf-8", xml_declaration=True)
    
def save_as_parquet(output_path, data):
    """
    Save the transcription and metadata to a .parquet file.

    :param output_path: Path to save the .parquet file
    :param data: Dict containing 'Input', 'Output', and 'Transcription Text'
    """
    # Flatten directly from already-normalized metadata
    flat_record = {
        **data.get("Input", {}),
        **data.get("Output", {}),
        "Transcription Text": data.get("Raw Text", "")
    }
    # Convert to one-row DataFrame and save
    df = pd.DataFrame([flat_record])
    df.to_parquet(output_path, index=False, engine="pyarrow")

def save_as_srt(output_path, merged_data):
    """
    Save transcript as SRT using segment-level DataFrame inside merged_data.
    """
    df = merged_data.get("DataFrame", None)

    if df is None or not hasattr(df, "iterrows"):
        raise ValueError("Missing or invalid DataFrame in merged_data for SRT export.")

    lines = []

    for i, row in df.iterrows():
        lines.append(str(i + 1))
        lines.append(f"{row['start_time']} --> {row['end_time']}")
        lines.append(row["text"].strip())
        lines.append("")  # blank line

    srt_path = os.path.splitext(output_path)[0] + ".srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[✅] SRT saved to: {srt_path}")
        
def save_as_vtt(output_path, merged_data):
    df = merged_data.get("DataFrame", None)

    if df is None or not hasattr(df, "iterrows"):
        raise ValueError("Missing or invalid DataFrame in merged_data for VTT export.")

    lines = ["WEBVTT", ""]

    for _, row in df.iterrows():
        lines.append(f"{row['start_time']} --> {row['end_time']}")
        lines.append(row["text"].strip())
        lines.append("")

    vtt_path = os.path.splitext(output_path)[0] + ".vtt"
    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[✅] VTT saved to: {vtt_path}")
    
SAVE_OUTPUT_FUNCTIONS = {
    "txt": save_as_txt,
    "json": save_as_json,
    "csv": save_as_csv,
    "xml": save_as_xml,
    "parquet": save_as_parquet,
    "srt": save_as_srt,
    "vtt": save_as_vtt,
}


# ────────────────────────────────────────────────
# Helper Methods
# ────────────────────────────────────────────────

def save_cluster_data(df, filename, format="feather"):
    """
    Save cluster data to a permanent /cluster_data directory for UI visualization.

    Parameters:
        df (pd.DataFrame): Must contain 'x', 'y', 'speaker_id'
        filename (str): Original filename (e.g., "call1.wav")
        format (str): 'feather' (default), or 'csv' for fallback
    """
    # 📂 Define permanent cluster data path
    cluster_dir = Path(__file__).resolve().parent.parent / "cluster_data"
    cluster_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(filename).stem
    save_path = cluster_dir / f"{stem}_umap.{format}"

    required_cols = {"x", "y", "speaker_id"}
    if not required_cols.issubset(df.columns):
        print(f"⚠️ Skipped saving cluster data — missing columns: {required_cols - set(df.columns)}")
        return

    try:
        if format == "feather":
            df[["x", "y", "speaker_id"]].reset_index(drop=True).to_feather(save_path)
        elif format == "csv":
            df[["x", "y", "speaker_id"]].to_csv(save_path, index=False)
        else:
            raise ValueError("Unsupported format: choose 'feather' or 'csv'")
        print(f"📁 Saved cluster data → {save_path}")
    except Exception as e:
        print(f"❌ Failed to save cluster data: {e}")
        

def _expand_key(compact_key):
    """
    Converts template keys like 'AudioFileName' to 'Audio File Name'
    to match metadata dictionary keys.
    """
    return " ".join([w for w in re.findall(r'[A-Z][a-z]*', compact_key)])

def timestamp_to_seconds(ts: str) -> float:
    """Converts 'HH:MM:SS.mmm' to total seconds."""
    t = datetime.datetime.strptime(ts, "%H:%M:%S.%f")
    return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1_000_000

def seconds_to_timestamp(seconds: float) -> str:
    """Converts seconds to 'HH:MM:SS.mmm' timestamp format."""
    return str(datetime.timedelta(seconds=seconds))[:-3]  # remove last 3 micro digits


def load_output_file(path):
    import os
    import pandas as pd
    import textwrap
    from tabulate import tabulate

    ext = os.path.splitext(path)[1].lower()

    # Load appropriate dataframe
    if ext == ".parquet":
        df = pd.read_parquet(path)
    elif ext == ".csv":
        df = pd.read_csv(path)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # Separate transcription (if present)
    transcription = ""
    if "Transcription Text" in df.columns:
        transcription = df["Transcription Text"].iloc[0]
        df = df.drop(columns=["Transcription Text"])

    # Generate one row of dtype info
    dtype_row = pd.DataFrame([df.dtypes.astype(str).tolist()], columns=df.columns)

    # Combine: dtypes first, then data rows
    combined_df = pd.concat([dtype_row, df], ignore_index=True)

    # Format using tabulate
    table_str = tabulate(combined_df, headers="keys", tablefmt="plain", showindex=False)

    # Optional wrapped transcription
    if transcription:
        wrapped = textwrap.fill(transcription, width=65)
        return f"{table_str}\n\nTranscription Text:\n{wrapped}"
    return table_str