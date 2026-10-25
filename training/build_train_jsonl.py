#!/usr/bin/env python3
"""Build Qwen3-TTS train_raw.jsonl from human-approved manifest rows."""
from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=Path("data/prepared/manifest.csv"))
    ap.add_argument("--output", type=Path, default=Path("data/training/train_raw.jsonl"))
    ap.add_argument("--min-segments", type=int, default=8)
    args = ap.parse_args()
    manifest = args.manifest.expanduser().resolve()
    if not manifest.is_file():
        raise SystemExit(f"Manifest not found: {manifest}. Run training/prepare_dataset.py first.")
    valid = []
    with manifest.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"audio", "text", "ref_audio", "approved"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise SystemExit(f"Manifest must contain columns: {', '.join(sorted(required))}")
        for line, row in enumerate(reader, start=2):
            if (row.get("approved") or "").strip().lower() not in {"yes", "y", "true", "1"}:
                continue
            text = " ".join((row.get("text") or "").split()).strip()
            audio = Path((row.get("audio") or "").strip()).expanduser()
            ref = Path((row.get("ref_audio") or "").strip()).expanduser()
            if not text:
                print(f"Skipping row {line}: empty transcript.", file=sys.stderr)
                continue
            if not audio.is_file() or not ref.is_file():
                raise SystemExit(f"Row {line} points to a missing audio/reference file: {audio} / {ref}")
            valid.append({"audio": str(audio.resolve()), "text": text, "ref_audio": str(ref.resolve())})
    if len(valid) < args.min_segments:
        raise SystemExit(f"Only {len(valid)} approved clips; minimum is {args.min_segments}. Review more clips; don't duplicate clips to inflate the dataset.")
    out = args.output.expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in valid:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(valid)} approved utterances to {out}")

if __name__ == "__main__":
    main()
