"""Speak a sentence the demo already produced.

The browser never receives the ElevenLabs key. This module does not
compose a new commercial number.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from app.databricks_backend import ROOT, _parse_env_file

VOICE_DEFAULT = "EXAVITQu4vr4xnSDxMaL"


class VoiceError(RuntimeError):
    pass


def _values(environ=None, env_file=None):
    import os

    if environ is None:
        environ = os.environ
    if env_file is None:
        env_file = ROOT / ".env"
    file_values = _parse_env_file(Path(env_file)) if env_file else {}

    def pick(key):
        return environ.get(key) or file_values.get(key) or ""

    return pick


def speak(text, environ=None, env_file=None):
    pick = _values(environ, env_file)
    key = pick("ELEVENLABS_API_KEY")
    voice = pick("ELEVENLABS_VOICE_ID") or VOICE_DEFAULT
    spoken = " ".join((text or "").split())
    if not spoken:
        raise VoiceError("Nothing to speak.")
    if not key:
        raise VoiceError("ElevenLabs is not configured. Set ELEVENLABS_API_KEY.")
    spoken = spoken[:1500]
    body = json.dumps({"text": spoken, "model_id": "eleven_turbo_v2_5"}).encode()
    request = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
        data=body,
        headers={
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            audio = response.read()
    except Exception as exc:
        raise VoiceError(f"ElevenLabs did not return audio. {type(exc).__name__}") from None
    if not audio:
        raise VoiceError("ElevenLabs returned an empty audio file.")
    return audio
