# **Transcribe Audio Service**

Transcribe Audio Service is a lightweight, standalone transcription tool for Windows.
Batch-converts audio files (.mp3, .m4a, and .wav) into readable text using OpenAI’s Whisper model — no technical setup required.

Users can choose between One Shot batch transcription or Continuous Directory Monitoring to automatically process new files at set intervals. Output formats include .txt, .csv, .json, and .xml, with optional translation to English for supported languages.

Designed for enterprise and academic users interested in rapid capture of accurate and configurable audio transcription data.

---

🚀 Features

    🖥️ Simple, standalone desktop app — no technical setup required

    🧠 Intelligent UI Design – users can effortlessly manage, deploy, and monitor their audio transcriptions through an intuitive user interface

    🤖 Powered by OpenAI’s Whisper — runs locally with high accuracy

    🎧 Supports .mp3, .m4a, and .wav audio formats

    🌐 Optional Translate → English feature for supported languages

    🔄 One Shot batch transcription or Continuous Directory Monitoring at custom intervals

    🗂️ Export transcripts as .txt, .json, .csv, or .xml

    🧾 Rich transcript metadata: filename, creation date, duration, audio language, output language, and more

    📂 Click-to-open completed files directly from the transcription queue

    🔊 Speaker recognition mode toggle (for future diarization support)

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
│   ├── constants.py                # Centralized constants (e.g., language map)
│   ├── dependency_check.py         # Optional: verifies installed dependencies
│   ├── template_manager.py         # Loads and injects templates for output formats
│   ├── transcription.py            # Whisper transcription logic
│   ├── utils.py                    # Metadata extraction + output writing
│   └── version.py                  # Application version constant
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

📦 Dependencies

openai-whisper

ffmpeg (external dependency)

ttkbootstrap

tkinter (standard library)

torch (automatically installed with Whisper)

---

📃 License
MIT License

---

🙌 Acknowledgements

OpenAI Whisper

ttkbootstrap

PyTorch

ffmpeg
