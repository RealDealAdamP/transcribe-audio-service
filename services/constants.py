# File: services/constants.py

WHISPER_MODELS = {
    "tiny":    {"default": "tiny",    "en": "tiny.en"},
    "base":    {"default": "base",    "en": "base.en"},
    "small":   {"default": "small",   "en": "small.en"},
    "medium":  {"default": "medium",  "en": "medium.en"},
    "large":   {"default": "large"},
    "turbo":   {"default": "turbo"}
}

MODEL_VRAM_REQUIREMENTS = {
    "tiny": 1,
    "base": 1.5,
    "small": 2,
    "medium": 5,
    "large": 10,
    "turbo": 6
}

# Recommended batch size thresholds based on available VRAM (in GB)
BATCH_SIZE_THRESHOLDS = {
    "high": {
        "vram": 10,        # GPUs with ≥10GB VRAM
        "batch_size": 32
    },
    "medium": {
        "vram": 8,         # GPUs with ≥8GB VRAM
        "batch_size": 16
    },
    "low": {
        "vram": 0,         # CPU or low-VRAM GPUs
        "batch_size": 8
    }
}


LANGUAGE_MAP = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Portuguese": "pt",
    "Italian": "it"
}

SPEAKER_LABEL_MAP = {
    "English": "SPEAKER",         # Common transcription convention
    "Spanish": "Interlocutor",    # Better suited than "Hablante" in conversations
    "French": "Intervenant",     # Standard in interviews, dialogues
    "German": "Sprecher",        # Used in captions/subtitles
    "Japanese": "話し手",           # (Hanashite) – the person who speaks
    "Portuguese": "Locutor",         # Used in broadcasting, subtitling
    "Italian": "Parlante",        # Common in linguistic/transcription contexts
}

SUPPORTED_AUDIO_EXTENSIONS = (
    ".mp3", ".m4a", ".wav", ".wma", ".flac", ".ogg",
    ".aac"
)

SUPPORTED_OUTPUT_EXTENSIONS = (
    "csv", "json", "txt", "xml", "parquet", "srt",
    "vtt"
)

FORMATS_REQUIRING_TEMPLATES = ("txt", "json", "xml", "csv")