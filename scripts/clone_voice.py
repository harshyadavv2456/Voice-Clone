#!/usr/bin/env python3
"""Decrypt an encrypted personal reference clip and generate cloned speech."""
from __future__ import annotations

import base64
import gc
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAX_TEXT_CHARS = 1_500
MAX_REFERENCE_SECONDS = 20
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
ASSET = Path("assets/voice-reference.mp3.enc.b64")
MAGIC = b"VCREF1\x00\x00"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def env(name: str, required: bool = True) -> str:
    value = os.environ.get(name, "").strip()
    if required and not value:
        fail(f"Required configuration is missing: {name}.")
    return value


def decrypt_reference(destination: Path) -> None:
    key_text = env("VOICE_SOURCE_KEY")
    try:
        key = base64.b64decode(key_text, validate=True)
    except Exception:
        fail("VOICE_SOURCE_KEY must be the base64 key supplied with this repository setup.")
    if len(key) != 32:
        fail("VOICE_SOURCE_KEY must decode to exactly 32 bytes.")
    if not ASSET.is_file():
        fail("Encrypted reference asset is missing from the repository.")
    try:
        payload = base64.b64decode(ASSET.read_bytes(), validate=True)
    except Exception:
        fail("Encrypted reference asset is not valid base64.")
    if len(payload) < len(MAGIC) + 12 + 16 or payload[:len(MAGIC)] != MAGIC:
        fail("Encrypted reference asset has an invalid format.")
    nonce = payload[len(MAGIC):len(MAGIC) + 12]
    ciphertext = payload[len(MAGIC) + 12:]
    try:
        raw_audio = AESGCM(key).decrypt(nonce, ciphertext, b"Voice-Clone reference v1")
    except Exception:
        fail("Could not unlock the encrypted reference. Check VOICE_SOURCE_KEY.")
    destination.write_bytes(raw_audio)
    del raw_audio, payload, ciphertext, key


def normalize_reference(source: Path, destination: Path) -> float:
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-i", str(source),
        "-t", str(MAX_REFERENCE_SECONDS), "-vn", "-ac", "1", "-ar", "24000",
        "-c:a", "pcm_s16le", str(destination),
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
        import soundfile as sf
        info = sf.info(str(destination))
    except Exception:
        fail("Could not decode the reference clip.")
    if info.duration < 3:
        fail("The reference clip is under 3 seconds; use a longer speech sample.")
    return float(info.duration)


def transcribe_reference(audio_path: Path) -> str:
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4, num_workers=1)
        segments, _ = model.transcribe(str(audio_path), beam_size=3, vad_filter=True)
        transcript = " ".join(s.text.strip() for s in segments if s.text.strip()).strip()
        del model
        gc.collect()
    except Exception:
        fail("Automatic transcription failed. Retry the workflow; no raw audio is uploaded.")
    if not transcript:
        fail("No speech detected in this segment. Try a different recording segment or ensure it contains clear speech.")
    return transcript


def main() -> None:
    text = env("TARGET_TEXT")
    language = env("OUTPUT_LANGUAGE")
    if len(text) > MAX_TEXT_CHARS:
        fail(f"Text must be {MAX_TEXT_CHARS} characters or fewer.")
    allowed = {"English", "Chinese", "Japanese", "Korean", "German", "French", "Russian", "Portuguese", "Spanish", "Italian"}
    if language not in allowed:
        fail("Unsupported language value.")

    work = Path("work")
    output = Path("output")
    work.mkdir(exist_ok=True)
    output.mkdir(exist_ok=True)
    source = work / "reference-source.mp3"
    ref_wav = work / "reference.wav"
    out_wav = output / "voice-output.wav"

    decrypt_reference(source)
    ref_duration = normalize_reference(source, ref_wav)
    # Remove the decrypted original as soon as the normalized reference exists.
    source.unlink(missing_ok=True)

    ref_text = transcribe_reference(ref_wav)
    try:
        import soundfile as sf
        import torch
        from qwen_tts import Qwen3TTSModel

        torch.set_num_threads(4)
        model = Qwen3TTSModel.from_pretrained(
            MODEL_ID,
            device_map="cpu",
            dtype=torch.float32,
            attn_implementation="sdpa",
        )
        waveforms, sample_rate = model.generate_voice_clone(
            text=text,
            language=language,
            ref_audio=str(ref_wav),
            ref_text=ref_text,
        )
        if not waveforms:
            fail("The model returned no audio.")
        sf.write(str(out_wav), waveforms[0], sample_rate)
        metadata = {
            "model": MODEL_ID,
            "language": language,
            "sample_rate": int(sample_rate),
            "reference_segment_seconds": round(ref_duration, 2),
            "mode": "reference-based zero-shot cloning; no model weights fine-tuned",
        }
        (output / "run-info.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        del model, waveforms
        gc.collect()
    except SystemExit:
        raise
    except Exception:
        fail("Qwen3-TTS generation failed on this CPU runner. See preceding dependency/model errors; raw audio is not uploaded.")
    print("Speech generation finished. The next workflow step encrypts the result before upload.")


if __name__ == "__main__":
    main()
