# Personal voice model: train, export, run locally

This project is intended to create a fine-tuned standalone Qwen3-TTS checkpoint from your own recordings. The existing GitHub Actions workflow is a separate reference-based voice-cloning demo and does not produce a personal model.

## Status

Open the [GPU training notebook in Colab](https://colab.research.google.com/github/harshyadavv2456/Voice-Clone/blob/main/training/voice_model_colab.ipynb) for the guided flow. Upload your own recordings to the notebook's private Google Drive dataset folder, review/correct the generated transcript manifest, then run fine-tuning and private export.


No personal checkpoint exists yet. This repo now has the fine-tuning and serving scripts, but actual training requires a CUDA GPU run. The current ~45-second reference recording is too small for a strong general-purpose personal voice model. A practical starting target is around 10–30 minutes of clean varied speech with transcripts corrected by a human; this is guidance, not a vendor-mandated minimum.

Official single-speaker fine-tuning docs: https://github.com/QwenLM/Qwen3-TTS/blob/main/finetuning/README.md

## 1. Prepare a private dataset

Keep your own recordings in data/raw/ and do not commit them to this public repository. Install FFmpeg and dependencies, then run:

    python3 -m pip install -r requirements.txt
    brew install ffmpeg
    python training/prepare_dataset.py --input-dir data/raw --output-dir data/prepared --whisper-model base --language en

This creates cleaned clips and data/prepared/manifest.csv. Check and correct each text transcript; set approved to YES only for correctly transcribed, clean samples. Rows marked NO are excluded. Then build the training JSONL:

    python training/build_train_jsonl.py --manifest data/prepared/manifest.csv --output data/training/train_raw.jsonl

## 2. Train on a CUDA GPU

Run this script in a Linux CUDA runtime such as a compatible Colab/Kaggle GPU session or rented GPU. Ensure PyTorch sees CUDA, then run:

    bash training/run_finetuning.sh

Default: Qwen3-TTS-12Hz-0.6B-Base, batch 2, learning rate 2e-5, 3 epochs, speaker name harsh_yadav. Settings can be changed with environment variables MODEL_ID, BATCH_SIZE, LEARNING_RATE, EPOCHS, SPEAKER_NAME, RAW_JSONL, OUTPUT_DIR. The script calls the official upstream prepare_data.py and sft_12hz.py training scripts. MacBook Air M5 is a local inference target, not the recommended environment for this CUDA training flow.

Check generated samples before treating any checkpoint as good. A fine-tune does not guarantee a perfect voice match.

## 3. Publish the full checkpoint privately

Create a Hugging Face write token and keep it secret. In the GPU runtime set HF_TOKEN in the environment, then run (change checkpoint path if needed):

    python training/publish_model.py --model-dir model-output/harsh-yadav-qwen3/checkpoint-epoch-2 --repo-id YOUR_HF_USERNAME/harsh-yadav-qwen3-voice

This creates a private model repository and uploads the complete checkpoint. Do not make it public; it can reproduce your voice.

## 4. Download and run locally

On your Mac:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r local-requirements.txt
    export HF_TOKEN=hf_your_private_token
    python training/download_model.py --repo-id YOUR_HF_USERNAME/harsh-yadav-qwen3-voice --local-dir models/harsh-yadav-qwen3-voice
    export VOICE_MODEL_PATH="$PWD/models/harsh-yadav-qwen3-voice"
    export VOICE_SPEAKER=harsh_yadav
    python serve_local.py

The server loads the fine-tuned model locally at http://127.0.0.1:8765. The first download may be several GB. Test with:

    curl -f http://127.0.0.1:8765/v1/audio/speech -H 'Content-Type: application/json' -d '{"input":"Hello from my personal voice model.","voice":"harsh_yadav","response_format":"wav"}' --output my-voice.wav
    open my-voice.wav

## 5. Reuse from other projects

GET /health reports readiness. POST /v1/audio/speech accepts JSON containing input, optional voice, and response_format=wav; it returns WAV bytes. Examples: clients/python_example.py and clients/node_example.mjs. Projects on the same Mac can call http://127.0.0.1:8765/v1/audio/speech. Cloud projects need a secured model-serving host; localhost is not reachable from the cloud. Do not expose this unauthenticated development API to the internet.

Keep raw recordings, model weights, tokens, and private keys out of Git. Use only your own voice or recordings you have permission to clone.