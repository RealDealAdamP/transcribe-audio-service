Transcribe Audio Service

Transcribe Audio Service is a lightweight, standalone transcription tool for Windows.  
It batch-converts audio files (`.mp3`,`.m4a`, and `.wav`) into readable text using OpenAI’s Whisper model — no technical setup required.

---

🚀 Features

- 🎯 Simple, intuitive desktop interface
- 🔁 Batch processing of large audio folders
- 🧠 Powered by OpenAI’s Whisper model (local inference)
- 💻 Fully offline — no cloud upload required
- ✅ Supports `.mp3` ,`.m4a`, and `.wav` formats

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
transcribe-audio-service/

├── main.py
├── gui/
│   ├── __init__.py
│   ├── app.py               # launch the GUI
│   ├── layout.py            # GUI layout & TranscribeAudioService class
│   ├── components.py        # (optional) reusable UI elements
├── services/
│   ├── __init__.py
│   ├── ffmpeg_check.py      # check if ffmpeg is installed
│   ├── transcription.py     # whisper logic & audio utils
│   ├── utils.py             # general helper methods

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
