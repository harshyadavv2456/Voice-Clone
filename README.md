# Voice-Clone

Free, open-source reference-voice cloning with the official Qwen3-TTS 0.6B Base checkpoint, using GitHub Actions for CPU inference. This repository contains source code and **encrypted** reference audio only—not a publicly playable voice recording.

## What this does

- Uses [Qwen3-TTS 0.6B Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base), under its model license (Apache-2.0).
- Stores the supplied reference clip as AES-256-GCM ciphertext in `assets/voice-reference.mp3.enc.b64`; the decryption key is provided separately as a GitHub Actions secret.
- Automatically transcribes the selected segment on the runner with Faster-Whisper, then generates speech in a similar voice.
- Encrypts generated audio to the repository owner's RSA public key before uploading a one-day artifact. The private output key is not in this repo.
- Does not fine-tune model weights. Qwen3-TTS Base performs reference-based zero-shot voice cloning at generation time.

## One-time setup

For the simplest setup, download and extract the private setup kit, then run `./finish_setup.sh`. It syncs this project, adds the encrypted reference asset, sets `VOICE_SOURCE_KEY` as an Actions secret, and stores the output private key in a local-only directory. Keep the kit private.

### 1. Add the source-audio secret

In this repository, open **Settings → Secrets and variables → Actions → New repository secret**. Create a repository secret with name `VOICE_SOURCE_KEY` and run `./finish_setup.sh` from the private setup kit, which uploads only the encrypted clip and stores its key as a repository secret. Alternatively, paste the single-line value from the private file `VOICE_SOURCE_KEY.txt`. This key decrypts only the encrypted source clip stored in this repository. Do not commit it or put it in workflow inputs.

### 2. Keep the output private key safe

Download and retain `VOICE_OUTPUT_PRIVATE.pem` in a private folder on your own device. **Never commit it or publish its contents.** The public counterpart (`keys/output_public.pem`) can safely remain in the public repository.

### 3. Run generation

1. Open **Actions → Clone my voice (encrypted output) → Run workflow**.
2. Enter the text you want generated and choose one of the listed languages.
4. Run the workflow and wait for it to complete. The first run downloads model weights and dependencies. The standard GitHub-hosted runner has CPU inference only, so generation may be slow or may hit the runner's memory/runtime limits.
5. Download the `encrypted-voice-output` artifact from the completed run and extract the artifact ZIP.

### 4. Decrypt output on your Mac

Install Python 3.11+ if needed and run:

```bash
python3 -m pip install cryptography
python3 scripts/decrypt_output.py /path/to/voice-output.vcenc \
  --private-key /private/path/VOICE_OUTPUT_PRIVATE.pem \
  --output-dir "$HOME/voice-clone-output"
open "$HOME/voice-clone-output/voice-output.wav"
```

If you downloaded only the artifact, download `scripts/decrypt_output.py` from this repository or use the script included in the repository clone. The raw WAV is decrypted locally, not committed.

## Privacy and safety

- The encrypted reference MP3 is public ciphertext, not playable audio; its key is supplied only as a repository Actions secret. The kit uses an eight-second reference segment selected from your uploaded recording and contains no plaintext audio. Do not share the secret or the private output key.
- The reference is decrypted only on the ephemeral workflow runner. The job removes working files and uploads encrypted output only; as with any hosted workflow, don't merge untrusted code into a workflow that reads secrets.
- Only use audio that you own or have explicit permission to clone. Do not impersonate another person, deceive listeners, or bypass voice authentication.
- GitHub Actions is not a permanently hosted web service and this workflow does not create a public audio API.

## Licenses and limits

This repository wrapper is MIT licensed. Qwen3-TTS model weights and other dependencies have their own licenses; see their official pages before commercial use. The Qwen3-TTS model card lists Chinese, English, Japanese, Korean, German, French, Russian, Portuguese, Spanish, and Italian; Hindi is not listed as supported. The result is a voice-cloning reference pipeline, not a fine-tuned personal model checkpoint.

## Official references

- [Qwen3-TTS source and usage](https://github.com/QwenLM/Qwen3-TTS)
- [Qwen3-TTS 0.6B Base model card and license](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base)
- [GitHub-hosted runner specifications](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
