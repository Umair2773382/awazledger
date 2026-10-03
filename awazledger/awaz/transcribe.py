"""Speech -> text.

Provider is picked by TRANSCRIBE_PROVIDER env var:
  groq  — free Groq API (whisper-large-v3-turbo). Default. Best quality,
           no local model download, server stays lightweight for free hosts.
           Needs GROQ_API_KEY (free at https://console.groq.com/keys).
  local — faster-whisper on this machine. Fully offline. First run downloads
           the model (WHISPER_MODEL, default 'small').
"""
import os

from .config import settings


def transcribe(audio_path: str) -> dict:
    """Return {'text': ..., 'language': ..., 'language_probability': ...}."""
    provider = os.getenv("TRANSCRIBE_PROVIDER", "groq").lower()
    if provider == "groq":
        return transcribe_groq(audio_path)
    return transcribe_local(audio_path)


def transcribe_groq(audio_path: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set — get a free key at https://console.groq.com/keys"
        )
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    with open(audio_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=f,
            language="ur",  # primary language; Whisper still handles mixed English
        )
    return {
        "text": resp.text.strip(),
        "language": "ur",
        "language_probability": 1.0,
    }


_model = None


def preload():
    """Load the local Whisper model (downloads on first run)."""
    from faster_whisper import WhisperModel

    global _model
    if _model is None:
        _model = WhisperModel(settings.whisper_model, compute_type="int8")
    return _model


def transcribe_local(audio_path: str) -> dict:
    model = preload()
    segments, info = model.transcribe(audio_path, language=None)  # auto-detect
    text = " ".join(s.text for s in segments).strip()
    return {
        "text": text,
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
    }
