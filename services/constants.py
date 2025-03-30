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


LANGUAGE_MAP = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Portuguese": "pt",
    "Italian": "it"
}