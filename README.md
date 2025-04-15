# **Transcribe Audio Service**

Transcribe Audio Service is a lightweight, standalone transcription tool for Windows that batch-converts audio files into readable text — no technical setup required.

Built on OpenAI’s Whisper models, it supports customizable transcription performance across tasks ranging from fast summaries to detailed archival records. Users can choose from multiple Whisper variants to optimize for speed, accuracy, or memory usage.

Supported input formats include .mp3, .m4a, .wav, .wma, .flac, .ogg, and .aac, offering broad compatibility for both academic and enterprise audio sources.

Two primary modes are available:

    One-Shot Batch Transcription – process all audio files in a selected directory.

    Continuous Monitoring – automatically transcribe new files added to a watched folder at user-defined intervals.

Output options include .txt, .csv, .json, and .xml, with optional translation to English for supported languages.

As of version 1.5.0, the app introduces automated speaker identification, using an unsupervised diarization pipeline to detect and label distinct speakers in multi-voice recordings.

Designed for configurability, speed, and reliability, Transcribe Audio Service is ideal for professionals who need accurate, scalable audio transcription without the overhead of cloud services or complex installs.

---

🚀 Features

    🖥️ Simple, standalone desktop app — no technical setup required

    🧠 Intelligent UI Design — effortlessly query, manage, export, and monitor audio transcriptions through an intuitive interface

    🤖 Transcriptions powered by [OpenAI’s Whisper](https://github.com/openai/whisper)** — select from all available models to balance speed, size, and accuracy

    🔊 Automated Speaker Identification — automatically detect and assign speaker labels 

    🎧 Supports .mp3, .m4a, .wav, .wma, .flac, .ogg, and .aac audio formats

    🌐 Optional Translate → English — available for supported languages

    🔄 One Shot transcription or Continuous Directory Monitoring — batch process or watch folders at custom intervals

    🗂️ Multiple output formats — export transcripts as pre formatted .txt, .json, .csv, or .xml 

    🧾 Rich transcript metadata — includes filename, creation date, duration, audio language, output language, and more

    📂 Click-to-open completed files — launch transcripts directly from the UI display

---

⚙️ Getting Started (Run from Source)

1. Clone the repository
git clone https://github.com/yourname/transcribe-audio-service.git
cd transcribe-audio-service

2. Create Virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows

3. Install dependencies
pip install -r requirements.txt

4. Run the app
python main.py

---

📁 Project Structure
<pre>

transcribe-audio-service/
│
├── main.py                         # Launches the GUI application
│
├── cfg/                            # Configuration and style profiles
│   ├── conf_debug                  # Debug mode settings
│   ├── conf_main                   # Default app settings
│   └── conf_style                  # Centralized style definitions (ttkbootstrap)
│
├── cluster_data/                   # Cached cluster outputs (.feather) for UMAP plots
│
├── gui/                            # Modular GUI components
│   ├── __init__.py
│   ├── app.py                      # Entry point for launching TranscribeAudioService
│   ├── device_monitor.py           # GPU/CPU live status polling
│   ├── queue_display.py            # File queue, status indicators, output box
│   ├── service_controls.py         # Transcribe, Stop, and status label controls
│   ├── settings_input.py           # Input panel (directory, language, monitoring)
│   ├── settings_model.py           # Model panel (model selection + speaker toggle)
│   ├── settings_output.py          # Output panel (directory, format, translation)
│   ├── ui_main.py                  # Main layout and control logic
│   └── ui_splash.py                # Animated splash screen with GPU readiness check
│
├── services/                       # Core services and business logic
│   ├── __init__.py
│   ├── dependency_check.py         # Optional: verifies installed dependencies
│   ├── template_manager.py         # Loads and injects output templates
│   ├── utils_audio.py              # Audio utilities (conversion, prepping, metadata)
│   ├── utils_debug.py              # Debug logging and error trace support
│   ├── utils_device.py             # Device selection, GPU fallback logic
│   ├── utils_diarize.py            # Unsupervised speaker diarization pipeline
│   ├── utils_models.py             # Whisper model loading and memory hints
│   ├── utils_output.py             # Output saving logic (txt, csv, json, xml, etc.)
│   ├── utils_transcribe.py         # Transcription orchestration, segmentation, formatting
│   └── version.py                  # Application version constant
│
├── templates/                      # Output templates for supported formats
│   ├── transcript_template.csv
│   ├── transcript_template.json
│   ├── transcript_template.txt
│   └── transcript_template.xml


.gitignore
LICENSE
requirements.txt 
README.md
</pre>
---

🧠 Diarization Pipeline (v1.5.0)

The speaker identification module uses an unsupervised diarization pipeline built on frame-level audio analysis, time aggregation, and density-based clustering.
📥 Input:

    Audio file: MP3 (pre-converted to 16kHz, 32kbps, mono)

    Whisper segments: Optional, used to tag frames with speech blocks for segment-level grouping

<pre>
Input: MP3 audio file (converted to 16kHz, 32kbps mono)
  |
  v
Step 0: Apply Silero VAD
    └─ Load with Librosa → generate voiced frame mask

  |
  v
Step 1: Extract Frame-Level Features
    └─ MFCCs, Spectral Contrast, f0, Chroma, etc.
    └─ Filter out non-voiced frames using VAD mask

  |
  v
Step 2: Normalize + Smooth
    └─ Rolling median filter + z-score scaling

  |
  v
Step 3: Tag Frames with Segments
    └─ Assign segment IDs to frames based on Whisper timing (if available)

  |
  v
Step 4: Time Aggregation
    └─ Aggregate features by fixed-length time bins (e.g., 1s) for clustering

  |
  v
Step 5: Frame Clustering
    └─ Reduce dimensions with UMAP (optional)
    └─ Cluster using HDBSCAN → assign `speaker_id` to each time bin

  |
  v
Step 6: Assign Speakers to Segments
    └─ Match clustered bins back to Whisper segments using overlap logic

  |
  v
Output:
    ├─ `segments`: Whisper segments with speaker labels
    ├─ `cluster_data`: clustered feature embeddings (`x`, `y`, `speaker_id`)
    └─ `diagnostics`: speaker summary by frame count (if enabled)
</pre>


🧾 Requirements
Python 3.9 or later
ffmpeg installed and in your system PATH (required by Whisper)

---

🧠 Whisper Model Specs
<pre>
Model	Size	Parameters	VRAM Required	Relative Speed	English-only	Multilingual
tiny	~39 MB	39M	~1 GB	~10× faster	✅ tiny.en	✅ tiny
base	~74 MB	74M	~1 GB	~7× faster	✅ base.en	✅ base
small	~244 MB	244M	~2 GB	~4× faster	✅ small.en	✅ small
medium	~769 MB	769M	~5 GB	~2× faster	✅ medium.en	✅ medium
large	~1.55 GB	1550M	~10 GB	1× (baseline)	❌	✅ large
turbo†	~809 MB	809M	~6 GB	~8× faster	❌	✅ turbo
</pre>
---

📦 Dependencies (for v1.5.0)

The following libraries and system tools are required to run Transcribe Audio Service.
🎙️ Core Transcription

    openai-whisper – Core transcription engine

    torch, torchaudio, torchvision – Model execution and GPU acceleration (CUDA 11.8)

🖥️ GUI Framework

    ttkbootstrap – Modern themed UI built on top of tkinter

    tkinter – Built-in with Python ≥ 3.9

🔊 Audio Processing

    ffmpeg – Required system dependency

        Must be installed separately and accessible in PATH

    librosa – Audio feature extraction (MFCCs, spectral contrast, etc.)

    silero-vad – Voice Activity Detection (VAD) to isolate speech frames

🧠 Speaker Diarization Pipeline

    umap-learn – Dimensionality reduction for high-dimensional feature vectors

    hdbscan – Unsupervised density-based clustering

⚙️ System Utilities

    psutil ≥ 5.9.0 – CPU/memory status reporting

    pynvml == 11.4.1 – NVIDIA GPU monitoring (stable with CUDA 11.x)

---

📃 License
MIT License

---

 🙌 Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) – for the powerful open-source speech identification models   
- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) – for modern, themeable UI components  
- [PyTorch](https://pytorch.org/) – for the deep learning backend powering both Whisper and Pyannote  
- [FFmpeg](https://ffmpeg.org/) – for robust, cross-platform audio and video processing  