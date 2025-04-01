# **Transcribe Audio Service**

Transcribe Audio Service is a lightweight, standalone transcription tool for Windows that batch-converts audio files into readable text — no technical setup required.

Harnessing the full range of OpenAI’s Whisper models, users can tailor transcription performance and accuracy to meet the needs of any task, from rapid summaries to detailed archival records.

Supported audio formats include .mp3, .m4a, .wav, .wma, .flac, .ogg, and .aac, providing robust compatibility for academic and enterprise use cases.

Users can choose between One Shot batch transcription or Continuous Directory Monitoring to automatically process new files at set intervals. Output formats include .txt, .csv, .json, and .xml, with optional translation to English for supported languages.

Version 1.4.0 introduces Automated Speaker Recognition, powered by Pyannote’s state-of-the-art diarization pipeline, enabling clearer attribution in multi-speaker environments.

Built with configurability and reliability in mind, this tool is ideal for professionals seeking accurate, flexible, and efficient audio transcription at scale.

---

🚀 Features

    🖥️ Simple, standalone desktop app — no technical setup required

    🧠 Intelligent UI Design — effortlessly manage, deploy, and monitor audio transcriptions through an intuitive interface

    🤖 Transcriptions powered by [OpenAI’s Whisper](https://github.com/openai/whisper)** — select from all available models to balance speed, size, and accuracy

    🔊 Automated Speaker Recognition powered by [Pyannote-Audio](https://github.com/pyannote/pyannote-audio)** — automatically detects and assigns speaker labels 

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
├── gui/                            # GUI components (modularized)
│   ├── __init__.py
│   ├── app.py                      # Entry point for launching TranscribeAudioService
│   ├── ui_main.py                  # Main layout and logic controller
│   ├── service_controls.py         # Transcribe, Stop, and service status label
│   ├── queue_display.py            # File queue, status indicators, and output box
│   ├── settings_input.py           # Input settings frame (directory, language, monitoring)
│   ├── settings_output.py          # Output settings frame (directory, format, translation)
│   ├── settings_model.py           # Model settings frame (model selection + speaker toggle)
│   └── style_config.py             # Centralized style definitions (ttkbootstrap)
│
├── services/                       # Core services and business logic
│   ├── __init__.py
│   ├── constants.py                # Centralized constants (e.g., language map, supported extensions)
│   ├── dependency_check.py         # Optional: verifies installed dependencies
│   ├── template_manager.py         # Loads and injects templates for output formats
│   ├── transcription.py            # Whisper transcription logic
│   ├── utils_audio.py              # Audio utilities (format conversion, prep)
│   ├── utils_transcribe.py         # Transcription utilities (device check, segmentation)
│   └── version.py                  # Application version constant
│
├── .models/                        # 🔒(Git-ignored) Local cache for Whisper + Pyannote models
│                                   # Automatically created/downloaded at runtime — not tracked in Git
│
├── cache_models/                   # 🔒(Git-ignored) Helper scripts to pre-cache models
│   └── cache_pyannote_model.py     # Used to download and store diarization models locally
│
├── templates/                      # Output templates for various formats
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

📦 Dependencies (for v1.4.0)

    openai-whisper – core transcription engine

    pyannote-audio – speaker diarization
    ↳ with [pyannote/speaker-diarization-3.1 pipeline](https://huggingface.co/pyannote/speaker-diarization-3.1)**

    mutagen – audio metadata extraction

    ttkbootstrap – modern themed UI for tkinter

    torch, torchaudio, torchvision – GPU support (CUDA 11.8 only)

    ffmpeg – required system dependency (must be installed separately and available in PATH)

    tkinter – included with standard Python installations (≥3.9)

---

📃 License
MIT License

---

 🙌 Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) – for the powerful open-source speech recognition models  
- [pyannote-audio](https://github.com/pyannote/pyannote-audio) – for enabling automated speaker diarization  
- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) – for modern, themeable UI components  
- [PyTorch](https://pytorch.org/) – for the deep learning backend powering both Whisper and Pyannote  
- [FFmpeg](https://ffmpeg.org/) – for robust, cross-platform audio and video processing  