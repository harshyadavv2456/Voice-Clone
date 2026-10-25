# Voice-Clone — Harsh's reusable personal voice model

This repo now has two separate paths:

1. The GitHub Actions workflow is a reference-based cloning demo. It does not create a personal trained model.
2. The new fine-tuning pipeline prepares your recordings, trains Qwen3-TTS 0.6B Base on a CUDA GPU, publishes the full checkpoint to a private Hugging Face model repository, downloads it to your Mac, and serves it with a reusable local HTTP API.

## Status and constraints

The full personal checkpoint has not been trained or produced yet. The source code and pipeline are set up, but the training job itself still needs to run successfully on a CUDA GPU. The existing ~45-second reference clip is not enough to expect a strong, broadly generalizing fine-tune. A practical initial dataset target is around 10–30 minutes of clean varied speech with corrected transcripts (guidance, not an official minimum). Official Qwen fine-tuning instructions: https://github.com/QwenLM/Qwen3-TTS/blob/main/finetuning/README.md

Follow training/README.md for the end-to-end steps: prepare a private speech dataset, check all transcripts, run fine-tuning on a CUDA GPU, upload the completed checkpoint to a private model repository, and download it for local inference.

## Reuse it in current and future projects

After the model has been trained and downloaded, run:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r local-requirements.txt
    export VOICE_MODEL_PATH="$PWD/models/harsh-yadav-qwen3-voice"
    export VOICE_SPEAKER=harsh_yadav
    python serve_local.py

The API binds to http://127.0.0.1:8765. Send POST requests to /v1/audio/speech with JSON such as {"input":"Hello from my app.","voice":"harsh_yadav","response_format":"wav"}; it returns a WAV file. See clients/README.md, clients/python_example.py, and clients/node_example.mjs. Projects running on the same Mac can call it; remote projects need a private, secured model-serving host because localhost is only local to that computer.

Raw recordings, model weights, Hugging Face tokens and private keys must not be committed to this public repo. The local API is unauthenticated and intended for localhost only; never expose it directly to the public internet. Only use your own voice or audio you have permission to clone.

References:
- Qwen3-TTS: https://github.com/QwenLM/Qwen3-TTS
- Fine-tuning guide: https://github.com/QwenLM/Qwen3-TTS/blob/main/finetuning/README.md
- 0.6B Base model card: https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base
