#!/usr/bin/env python3
"""Example: call the local voice service from any Python project."""
from pathlib import Path
import requests

BASE_URL = "http://127.0.0.1:8765"

def speak(text: str, output_file: str | Path = "speech.wav", language: str = "English") -> Path:
    response = requests.post(
        f"{BASE_URL}/v1/audio/speech",
        json={"model": "harsh-voice", "input": text, "voice": "harsh_yadav",
              "language": language, "response_format": "wav"},
        timeout=600,
    )
    response.raise_for_status()
    path = Path(output_file)
    path.write_bytes(response.content)
    return path

if __name__ == "__main__":
    out = speak("Hello from my locally hosted personal voice model.")
    print(f"Saved {out.resolve()}")
