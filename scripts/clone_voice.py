#!/usr/bin/env python3
"""Decrypt private reference audio and synthesize text with Qwen3-TTS."""
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
    text, language, key_text = required("TARGET_TEXT"), required("OUTPUT_LANGUAGE"), required("VOICE_SOURCE_KEY")
    if len(text) > 1500: fail("Text must be 1,500 characters or fewer.")
    if language not in LANGUAGES: fail("Unsupported language.")
    try:
        key = base64.b64decode(key_text, validate=True)
        payload = base64.b64decode(ASSET.read_bytes(), validate=True)
        if len(key) != 32 or payload[:8] != MAGIC: raise ValueError()
        audio = AESGCM(key).decrypt(payload[8:20], payload[20:], b"Voice-Clone reference v1")
    except Exception:
        fail("Could not decrypt reference. Check VOICE_SOURCE_KEY and encrypted asset.")
    work, out = Path("work"), Path("output")
    work.mkdir(exist_ok=True); out.mkdir(exist_ok=True)
    source, ref = work / "source.mp3", work / "reference.wav"
    source.write_bytes(audio)
    del audio, payload, key
    try:
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-i",str(source),"-t","20","-vn","-ac","1","-ar","24000","-c:a","pcm_s16le",str(ref)], check=True, timeout=90)
        import soundfile as sf
        if sf.info(str(ref)).duration < 3: fail("Reference clip is shorter than 3 seconds.")
    except SystemExit: raise
    except Exception: fail("Could not normalize encrypted reference audio.")
    finally: source.unlink(missing_ok=True)
    try:
        from faster_whisper import WhisperModel
        whisper = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=2, num_workers=1)
        segments, _ = whisper.transcribe(str(ref), beam_size=3, vad_filter=True)
        ref_text = " ".join(s.text.strip() for s in segments if s.text.strip()).strip()
        del whisper; gc.collect()
        if not ref_text: fail("No speech detected in the reference clip.")
        import torch, soundfile as sf
        from qwen_tts import Qwen3TTSModel
        torch.set_num_threads(2)
        model = Qwen3TTSModel.from_pretrained(MODEL_ID, device_map="cpu", dtype=torch.float32, attn_implementation="sdpa")
        waveforms, sample_rate = model.generate_voice_clone(text=text, language=language, ref_audio=str(ref), ref_text=ref_text)
        if not waveforms: fail("The model returned no audio.")
        sf.write(str(out / "voice-output.wav"), waveforms[0], sample_rate)
        (out / "run-info.json").write_text(json.dumps({"model": MODEL_ID, "language": language, "reference_transcript": ref_text, "mode": "reference-based zero-shot cloning; no weight fine-tuning"}, indent=2) + "\n")
        del model, waveforms; gc.collect()
    except SystemExit: raise
    except Exception as exc:
        print(f"Generation error type: {type(exc).__name__}", file=sys.stderr)
        fail("Speech generation failed on the CPU runner. Inspect prior log messages for model/dependency details.")
    finally: ref.unlink(missing_ok=True)

if __name__ == "__main__": main()
