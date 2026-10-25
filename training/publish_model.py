#!/usr/bin/env python3
"""Upload a trained full checkpoint to a private Hugging Face model repository."""
from __future__ import annotations
import argparse, os
from pathlib import Path

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-dir", type=Path, required=True, help="A complete checkpoint-epoch-N directory.")
    ap.add_argument("--repo-id", required=True, help="Hugging Face repo id, e.g. username/harsh-yadav-qwen3-voice.")
    args = ap.parse_args()
    model_dir = args.model_dir.expanduser().resolve()
    if not model_dir.is_dir() or not (model_dir / "config.json").is_file():
        raise SystemExit(f"Expected a complete model checkpoint containing config.json: {model_dir}")
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise SystemExit("Set HF_TOKEN in your environment using a Hugging Face write token. Never commit it.")
    try:
        from huggingface_hub import HfApi
    except ImportError as exc:
        raise SystemExit("Install dependency: pip install huggingface_hub") from exc
    api = HfApi(token=token)
    api.create_repo(repo_id=args.repo_id, repo_type="model", private=True, exist_ok=True)
    api.upload_folder(repo_id=args.repo_id, repo_type="model", folder_path=str(model_dir),
                      commit_message="Upload trained personal Qwen3-TTS voice checkpoint",
                      ignore_patterns=["*.tmp", "*.lock", "optimizer.pt", "scheduler.pt", "rng_state.pth"])
    print(f"Uploaded model to private repository: https://huggingface.co/{args.repo_id}")
    print("Keep the repository private if the checkpoint encodes your identity.")

if __name__ == "__main__":
    main()
