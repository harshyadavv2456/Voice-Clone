# Voice-Clone

Free reference-based voice cloning using Qwen3-TTS 0.6B Base with GitHub Actions CPU inference. The public repository contains code and encrypted reference audio, not playable personal audio.

## Setup (one-time)
1. Open Settings → Secrets and variables → Actions → New repository secret.
2. Create VOICE_SOURCE_KEY; paste the one-line value from the private file VOICE_SOURCE_KEY.txt supplied alongside this setup. Never commit that key.
3. Download and keep VOICE_OUTPUT_PRIVATE.pem on your own device. Never commit or share it.
4. Open Actions → Clone my voice (encrypted output) → Run workflow. Enter the text and choose a language.
5. Download the encrypted-voice-output artifact from the completed run. Unzip it, then decrypt it locally using Python 3.11+ and the cryptography package:
   python3 -m pip install cryptography
   python3 scripts/decrypt_output.py /path/to/voice-output.vcenc --private-key /private/path/VOICE_OUTPUT_PRIVATE.pem --output-dir "$HOME/voice-clone-output"
   open "$HOME/voice-clone-output/voice-output.wav"

## Privacy
The reference clip in assets/voice-reference.mp3.enc.b64 is AES-256-GCM encrypted. Its key is not in this repository and must be set as an Actions secret. Generated speech is encrypted with the public key in keys/output_public.pem before artifact upload; only the private output key can decrypt it. The workflow removes raw audio from its temporary runner and retains the encrypted artifact for one day. Review every workflow change before running with secrets.

## Model and limitations
The model is Qwen/Qwen3-TTS-12Hz-0.6B-Base (Apache-2.0 model license). It clones by conditioning on the supplied audio; it does not fine-tune or create new model weights. GitHub-hosted runners are CPU-only for this workflow, so first-run downloads and synthesis may be slow or can exceed memory/runtime limits. Qwen3-TTS lists Chinese, English, Japanese, Korean, German, French, Russian, Portuguese, Spanish, and Italian; Hindi is not listed as supported. Check each dependency's license before commercial use.

Only clone voices you own or have explicit permission to use. Do not impersonate someone, deceive listeners, or bypass voice authentication.

References: https://github.com/QwenLM/Qwen3-TTS and https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base
