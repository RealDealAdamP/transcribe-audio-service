# File: transcribe_audio_service/services/utils_audio.py



import torchaudio
import subprocess
import tempfile
import os

WHISPER_SAMPLE_RATE = 16000

def prep_whisper_audio(path, temp_dir, target_sr=12000, bitrate="16k"):
    """
    Convert audio to optimized MP3 format for Whisper using FFmpeg.

    Returns:
        str: Path to the newly converted MP3 file.
    """
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir=temp_dir) as tmp:
        compressed_mp3_path = tmp.name

    command = [
        "ffmpeg", "-i", path,
        "-ac", "1",                   # mono
        "-ar", str(target_sr),       # sample rate
        "-b:a", bitrate,             # bit rate
        "-f", "mp3",
        compressed_mp3_path,
        "-y"
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return compressed_mp3_path

def prep_pyannote_audio(path, temp_dir, target_sr=16000):
    """
    Converts an input audio file to a 16kHz mono WAV format suitable for PyAnnote.

    Returns:
        Tuple[Tensor, int]: waveform [1, N], sample_rate
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir=temp_dir) as tmp:
        temp_wav_path = tmp.name

    # Use ffmpeg to convert to a PyAnnote-compatible .wav
    command = [
        "ffmpeg", "-i", path,
        "-ac", "1",                  # mono
        "-ar", str(target_sr),      # 16kHz
        "-acodec", "pcm_s16le",     # raw PCM
        temp_wav_path,
        "-y"
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Load the result into memory
    waveform, sample_rate = torchaudio.load(temp_wav_path)

    # Clean up the temp file now that we're done
    os.remove(temp_wav_path)

    return waveform, sample_rate


