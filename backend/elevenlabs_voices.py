"""
ElevenLabs voice agent integration.

Provides top 10 male and female ElevenLabs voices for text-to-speech generation.
The API key is read from the ELEVENLABS_API_KEY environment variable (or passed
per-request).
"""

import os
import io
from typing import List, Optional

# ---------------------------------------------------------------------------
# Top 10 male and female ElevenLabs premade voices
# Voice IDs sourced from the ElevenLabs premade-voices catalogue.
# ---------------------------------------------------------------------------

ELEVENLABS_MALE_VOICES: List[dict] = [
    {
        "voice_id": "pNInz6obpgDQGcFmaJgB",
        "name": "Adam",
        "gender": "male",
        "accent": "american",
        "description": "Deep, middle-aged, authoritative",
        "use_case": "narration",
    },
    {
        "voice_id": "ErXwobaYiN019PkySvjV",
        "name": "Antoni",
        "gender": "male",
        "accent": "american",
        "description": "Well-rounded, warm",
        "use_case": "narration",
    },
    {
        "voice_id": "VR6AewLTigWG4xSOukaG",
        "name": "Arnold",
        "gender": "male",
        "accent": "american",
        "description": "Crisp, confident",
        "use_case": "narration",
    },
    {
        "voice_id": "N2lVS1w4EtoT3dr4eOWO",
        "name": "Callum",
        "gender": "male",
        "accent": "american",
        "description": "Intense, nerdy",
        "use_case": "characters",
    },
    {
        "voice_id": "IKne3meq5aSn9XLyUdCD",
        "name": "Charlie",
        "gender": "male",
        "accent": "australian",
        "description": "Casual, conversational",
        "use_case": "conversational",
    },
    {
        "voice_id": "2EiwWnXFnvU5JabPnv8n",
        "name": "Clyde",
        "gender": "male",
        "accent": "american",
        "description": "Middle-aged war veteran",
        "use_case": "characters",
    },
    {
        "voice_id": "onwK4e9ZLuTAKqWW03F9",
        "name": "Daniel",
        "gender": "male",
        "accent": "british",
        "description": "Deep, authoritative, news presenter",
        "use_case": "news",
    },
    {
        "voice_id": "g5CIjZEefAph4nQFvHAz",
        "name": "Ethan",
        "gender": "male",
        "accent": "american",
        "description": "Soft, whisper-like",
        "use_case": "asmr",
    },
    {
        "voice_id": "SOYHLrjzK2X1ezoPC6cr",
        "name": "Harry",
        "gender": "male",
        "accent": "british",
        "description": "Anxious, energetic",
        "use_case": "characters",
    },
    {
        "voice_id": "TX3LPaxmHKxFdv7VOQHJ",
        "name": "Liam",
        "gender": "male",
        "accent": "american",
        "description": "Clear, articulate for narration",
        "use_case": "narration",
    },
]

ELEVENLABS_FEMALE_VOICES: List[dict] = [
    {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "name": "Rachel",
        "gender": "female",
        "accent": "american",
        "description": "Calm, professional narrator",
        "use_case": "narration",
    },
    {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "name": "Bella",
        "gender": "female",
        "accent": "american",
        "description": "Soft, creative",
        "use_case": "narration",
    },
    {
        "voice_id": "AZnzlk1XvdvUeBnXmlld",
        "name": "Domi",
        "gender": "female",
        "accent": "american",
        "description": "Strong, bold",
        "use_case": "narration",
    },
    {
        "voice_id": "MF3mGyEYCl7XYWbV9V6O",
        "name": "Elli",
        "gender": "female",
        "accent": "american",
        "description": "Emotional, expressive, young",
        "use_case": "characters",
    },
    {
        "voice_id": "LcfcDJNUP1GQjkzn1xUU",
        "name": "Emily",
        "gender": "female",
        "accent": "american",
        "description": "Calm, whisper-like",
        "use_case": "meditation",
    },
    {
        "voice_id": "XB0fDUnXU5powFXDhCwa",
        "name": "Charlotte",
        "gender": "female",
        "accent": "british",
        "description": "Conversational, warm, seductive",
        "use_case": "conversational",
    },
    {
        "voice_id": "jsCqWAovK2LkecY7zXl4",
        "name": "Freya",
        "gender": "female",
        "accent": "american",
        "description": "Warm, overly expressive",
        "use_case": "characters",
    },
    {
        "voice_id": "pFZP5JQG7iQjIQuC4Bku",
        "name": "Lily",
        "gender": "female",
        "accent": "british",
        "description": "Warm, pleasant narrator",
        "use_case": "narration",
    },
    {
        "voice_id": "piTKgcLEGmPE4e6mEKli",
        "name": "Nicole",
        "gender": "female",
        "accent": "american",
        "description": "Soft whisper, intimate",
        "use_case": "asmr",
    },
    {
        "voice_id": "ThT5KcBeYPX3keUQqHPh",
        "name": "Dorothy",
        "gender": "female",
        "accent": "british",
        "description": "Pleasant, expressive, children's stories",
        "use_case": "children_stories",
    },
]

# Combined catalogue
ALL_VOICES: List[dict] = ELEVENLABS_MALE_VOICES + ELEVENLABS_FEMALE_VOICES


def get_all_voices() -> List[dict]:
    """Return all pre-configured ElevenLabs voices (10 male + 10 female)."""
    return ALL_VOICES


def get_voice_by_id(voice_id: str) -> Optional[dict]:
    """Look up a voice by its ElevenLabs voice_id."""
    for voice in ALL_VOICES:
        if voice["voice_id"] == voice_id:
            return voice
    return None


def get_api_key(api_key: Optional[str] = None) -> str:
    """
    Resolve the ElevenLabs API key.

    Priority:
    1. ``api_key`` argument (per-request override)
    2. ``ELEVENLABS_API_KEY`` environment variable

    Raises:
        ValueError: if no API key can be found.
    """
    key = api_key or os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise ValueError(
            "ElevenLabs API key is required. Set the ELEVENLABS_API_KEY environment "
            "variable or pass api_key in the request body."
        )
    return key


def generate_speech(
    text: str,
    voice_id: str,
    api_key: Optional[str] = None,
    model_id: str = "eleven_multilingual_v2",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    style: float = 0.0,
    use_speaker_boost: bool = True,
) -> bytes:
    """
    Generate speech using the ElevenLabs TTS API (synchronous).

    Args:
        text: Input text (the "vector") to convert to speech.
        voice_id: ElevenLabs voice ID to use.
        api_key: Optional API key override; falls back to ELEVENLABS_API_KEY env var.
        model_id: ElevenLabs model to use (default: eleven_multilingual_v2).
        stability: Voice stability (0.0–1.0).
        similarity_boost: Similarity boost (0.0–1.0).
        style: Style exaggeration (0.0–1.0).
        use_speaker_boost: Whether to use speaker boost.

    Returns:
        Raw MP3 audio bytes.

    Raises:
        ValueError: If no API key is configured or voice_id is unknown.
        RuntimeError: If the ElevenLabs API call fails.
    """
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings

    resolved_key = get_api_key(api_key)

    if not get_voice_by_id(voice_id):
        raise ValueError(
            f"Voice '{voice_id}' is not in the pre-configured voice catalogue. "
            "Use GET /agent/elevenlabs/voices to list valid voice IDs."
        )

    client = ElevenLabs(api_key=resolved_key)

    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=model_id,
        voice_settings=VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost,
            style=style,
            use_speaker_boost=use_speaker_boost,
        ),
        output_format="mp3_44100_128",
    )

    # The SDK returns a generator of bytes chunks; collect them all.
    buffer = io.BytesIO()
    for chunk in audio_stream:
        buffer.write(chunk)

    return buffer.getvalue()
