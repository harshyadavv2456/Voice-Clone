#!/usr/bin/env python3
"""Decrypt encrypted reference audio and generate speech using Qwen3-TTS."""
from __future__ import annotations
import base64, gc, json, os, subprocess, sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
ASSET = Path("assets/voice-reference.mp3.enc.b64")
MAGIC = b"VCREF1\x00\x00"
LANGUAGES = {"English", "Chinese", "Japanese", "Korean", "German", "French", "Russian", "Portuguese", "Spanish", "Italian"}

def fail(message: str) -> None:
    print("ERROR: " + message, file=sys.stderr)
    raise SystemExit(1)

def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        fail("Required Actions secret/input is missing: " + name)
    return value

def main() -> None:
    text = required("TARGET_TEXT")
    language = required("OUTPUT_LANGUAGE")
    key_text = required("VOICE_SOURCE_KEY")
    if len(text) > 1500:
        fail("Text must be 1,500 characters or fewer.")
    if language not in LANGUAGES:
        fail("Unsupported language.")
    try:
        key = base64.b64decode(key_text, validate=True)
        if len(key) != 32:
            raise ValueError("wrong key length")
        payload = base64.b64decode(ASSET.read_bytes(), validate=True)
        if payload[:8] != MAGIC:
            raise ValueError("bad encrypted asset")
        nonce, ciphertext = payload[8:20], payload[20:]
        audio = AESGCM(key).decrypt(nonce, ciphertext, b"Voice-Clone reference v1")
    except Exception:
        fail("Could not decrypt the reference. Check VOICE_SOURCE_KEY and the encrypted asset.")
    work, out = Path("work"), Path("output")
    work.mkdir(exist_ok=True); out.mkdir(exist_ok=True)
    source, ref, target = work / "source.mp3", work / "reference.wav", out / "voice-output.wav"
    source.write_bytes(audio)
    del audio, payload, ciphertext, key
    try:
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-i",str(source),"-t","20","-vn","-ac","1","-ar","24000","-c:a","pcm_s16le",str(ref)], check=True, timeout=90)
        import soundfile as sf
        if sf.info(str(ref)).duration < 3:
            fail("The reference clip is shorter than 3 seconds.")
    except SystemExit:
        raise
    except Exception:
        fail("Could not normalize the encrypted reference clip.")
    source.unlink(missing_ok=True)
    try:
        from faster_whisper import WhisperModel
        whisper = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4, num_workers=1)
        segments, _ = whisper.transcribe(str(ref), beam_size=3, vad_filter=True)
        ref_text = " ".join(s.text.strip() for s in segments if s.text.strip()).strip()
        del whisper
        gc.collect()
        if not ref_text:
            fail("No speech detected. The encrypted reference segment may contain silence.")
        import torch
        from qwen_tts import Qwen3TTSModel
        torch.set_num_threads(4)
        model = Qwen3TTSModel.from_pretrained(MODEL_ID, device_map="cpu", dtype=torch.float32, attn_implementation="sdpa")
        waveforms, sample_rate = model.generate_voice_clone(text=text, language=language, ref_audio=str(ref), ref_text=ref_text)
        if not waveforms:
            fail("The model returned no audio.")
        sf.write(str(target), waveforms[0], sample_rate)
        (out / "run-info.json").write_text(json.dumps({"model": MODEL_ID, "language": language, "reference_seconds": round(sf.info(str(ref)).duration,2), "mode": "reference-based zero-shot cloning; no weight fine-tuning"}, indent=2) + "\n")
        del model, waveforms
        gc.collect()
    except SystemExit:
        raise
    except Exception:
        fail("Speech generation failed on the CPU runner. Check dependency/model download errors.")
    finally:
        ref.unlink(missing_ok=True)
    print("Generation completed; output encryption runs next.")

if __name__ == "__main__":
    main()
