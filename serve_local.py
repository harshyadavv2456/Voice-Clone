#!/usr/bin/env python3
"""Serve a locally stored fine-tuned Qwen3-TTS personal voice model over HTTP."""
from __future__ import annotations
import io, os, threading
from pathlib import Path
import soundfile as sf
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from qwen_tts import Qwen3TTSModel

MODEL_PATH = Path(os.environ.get("VOICE_MODEL_PATH", "models/harsh-yadav-qwen3-voice")).expanduser()
SPEAKER_NAME = os.environ.get("VOICE_SPEAKER", "harsh_yadav")
DEFAULT_LANGUAGE = os.environ.get("VOICE_LANGUAGE", "English")
HOST = os.environ.get("VOICE_API_HOST", "127.0.0.1")
PORT = int(os.environ.get("VOICE_API_PORT", "8765"))

if not MODEL_PATH.exists():
    raise SystemExit(f"Trained model not found: {MODEL_PATH}. Set VOICE_MODEL_PATH to the fine-tuned checkpoint directory.")

def choose_device_and_dtype():
    if torch.cuda.is_available():
        return "cuda:0", (torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16)
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps", torch.float32
    return "cpu", torch.float32

DEVICE, DTYPE = choose_device_and_dtype()
print(f"Loading voice model from {MODEL_PATH} on {DEVICE}...")
model = Qwen3TTSModel.from_pretrained(str(MODEL_PATH), device_map=DEVICE, dtype=DTYPE,
                                      attn_implementation="sdpa")
print("Personal voice model loaded.")
app = FastAPI(title="Personal Voice API", version="1.0.0")
_generation_lock = threading.Lock()

class SpeechRequest(BaseModel):
    model: str = "harsh-voice"
    input: str = Field(min_length=1, max_length=5000)
    voice: str = SPEAKER_NAME
    language: str = DEFAULT_LANGUAGE
    response_format: str = "wav"

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": True, "device": DEVICE,
            "speaker": SPEAKER_NAME, "language": DEFAULT_LANGUAGE}

@app.post("/v1/audio/speech")
def create_speech(req: SpeechRequest):
    if req.response_format.lower() not in {"wav", "wave"}:
        raise HTTPException(status_code=400, detail="This local endpoint currently supports response_format='wav' only.")
    text = req.input.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    try:
        with _generation_lock:
            wavs, sample_rate = model.generate_custom_voice(
                text=text, language=req.language, speaker=req.voice
            )
        if not wavs:
            raise RuntimeError("The model returned no waveform.")
        buff = io.BytesIO()
        sf.write(buff, wavs[0], int(sample_rate), format="WAV")
        return Response(content=buff.getvalue(), media_type="audio/wav",
                        headers={"Content-Disposition": 'attachment; filename="voice.wav"'})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Voice generation failed: {type(exc).__name__}: {exc}") from exc

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
