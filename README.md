Transcribe Audio Service

Transcribe Audio Service is a lightweight, standalone transcription tool for Windows.  
It batch-converts audio files (`.mp3`,`.m4a`, and `.wav`) into readable text using OpenAI’s Whisper model — no technical setup required.

---

🚀 Features

    🖥️ Easy-to-use desktop interface for transcribing audio files

    🔄 Batch processing of .mp3, .m4a, and .wav files

    🤖 Local transcription powered by OpenAI’s Whisper — no internet required

    📁 Choose from 4 output formats: .txt, .json, .csv, .xml

    📝 Each transcript includes metadata like filename, creation date, and transcription time

    🔊 Optional speaker recognition mode (for future enhancements)

    📂 Easily refresh and update the transcribe queue

    🧾 Open transcript files directly by double-clicking completed items

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

<pre>
📁 Project Structure
<pre>
transcribe-audio-service/
│
├── main.py                         # Launches the GUI application
│
├── gui/                            # GUI components (modularized)
│   ├── __init__.py
│   ├── app.py                     # Entry point for launching TranscribeAudioService
│   ├── layout.py                  # Main layout and logic controller
│   ├── button_controls.py         # UI buttons: Transcribe, Stop, Status label
│   ├── queue_display.py           # File queue, status indicators, and output box
│   ├── settings_panel.py          # Radio buttons + checkboxes for settings
│   └── style_config.py            # Centralized style definitions (ttkbootstrap)
│
├── services/                       # Core services and business logic
│   ├── __init__.py
│   ├── dependency_check.py        # Optional: verifies installed dependencies
│   ├── template_manager.py        # Loads and injects templates for output formats
│   ├── transcription.py           # Whisper transcription logic
│   ├── utils.py                   # Metadata extraction + output writing
│   └── version.py                 # Application version constant
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
