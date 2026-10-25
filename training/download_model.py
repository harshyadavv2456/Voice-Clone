#!/usr/bin/env python3
"""Download the complete trained voice checkpoint from a Hugging Face model repo."""
from __future__ import annotations
import argparse, os
from pathlib import Path

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-id", required=True, help="username/harsh-yadav-qwen3-voice")
    ap.add_argument("--local-dir", type=Path, default=Path("models/harsh-yadav-qwen3-voice"))
    args = ap.parse_args()
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise SystemExit("Install local-requirements.txt first.") from exc
    path = snapshot_download(repo_id=args.repo_id, repo_type="model",
                             local_dir=str(args.local_dir.expanduser().resolve()),
                             token=os.environ.get("HF_TOKEN") or None)
    print(f"Downloaded full checkpoint to {path}")
    print("Keep model weights private; the model can reproduce your voice.")

if __name__ == "__main__":
    main()
