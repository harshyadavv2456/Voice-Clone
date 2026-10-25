#!/usr/bin/env python3
"""Transcribe source recordings and split them into reviewable TTS training clips.

The generated manifest is deliberately NOT approved for training until a human
has checked each transcript.
"""
from __future__ import annotations
import argparse, csv, subprocess
from pathlib import Path

AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".mp4", ".webm"}

def run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:
        raise SystemExit("ffmpeg is required. Install it with: brew install ffmpeg") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Audio conversion failed: {(exc.stderr or '')[-1200:]}") from exc

def normalize(source: Path, destination: Path, seconds: float = 10.0) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-i", str(source),
         "-t", str(seconds), "-vn", "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(destination)])

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir", type=Path, required=True, help="Folder of your own recordings.")
    ap.add_argument("--output-dir", type=Path, default=Path("data/prepared"))
    ap.add_argument("--reference-audio", type=Path, default=None, help="Optional clean reference clip.")
    ap.add_argument("--whisper-model", default="base", help="tiny, base, small, medium, or large-v3")
    ap.add_argument("--min-seconds", type=float, default=2.5)
    ap.add_argument("--max-seconds", type=float, default=15.0)
    ap.add_argument("--language", default="en")
    args = ap.parse_args()
    source_dir, out_dir = args.input_dir.expanduser().resolve(), args.output_dir.expanduser().resolve()
    clips_dir = out_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    sources = sorted(p for p in source_dir.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTS)
    if not sources:
        raise SystemExit(f"No supported audio files found in {source_dir}")
    if args.min_seconds <= 0 or args.max_seconds <= args.min_seconds:
        raise SystemExit("Invalid segment duration limits.")
    reference_src = args.reference_audio.expanduser().resolve() if args.reference_audio else sources[0]
    if not reference_src.is_file():
        raise SystemExit(f"Reference audio does not exist: {reference_src}")
    ref_path = out_dir / "reference.wav"
    normalize(reference_src, ref_path, 10.0)
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SystemExit("Missing dependency: pip install faster-whisper") from exc
    print(f"Transcribing {len(sources)} recording(s) with faster-whisper '{args.whisper_model}'...")
    model = WhisperModel(args.whisper_model, device="cpu", compute_type="int8")
    rows, idx = [], 0
    for src in sources:
        print(f"  -> {src.name}")
        segments, _ = model.transcribe(str(src), language=args.language, beam_size=5,
                                       vad_filter=True, condition_on_previous_text=False)
        for seg in segments:
            text = " ".join((seg.text or "").split()).strip()
            start, end = max(0.0, float(seg.start)), max(0.0, float(seg.end))
            duration = end - start
            if not text or duration < args.min_seconds or duration > args.max_seconds:
                continue
            idx += 1
            clip_path = clips_dir / f"utt_{idx:05d}.wav"
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                 "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{duration:.3f}", "-vn",
                 "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(clip_path)])
            rows.append({"audio": str(clip_path.resolve()), "text": text,
                         "ref_audio": str(ref_path.resolve()), "approved": "NO",
                         "source": str(src), "start_s": f"{start:.3f}", "end_s": f"{end:.3f}"})
    del model
    manifest = out_dir / "manifest.csv"
    fields = ["audio", "text", "ref_audio", "approved", "source", "start_s", "end_s"]
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {len(rows)} clips and manifest: {manifest}")
    print("Correct every transcript. Change approved=NO to YES only for clean clips with verified text.")
    if len(rows) < 30:
        print("WARNING: small dataset. A practical starting target for a strong personal model is around 10–30 minutes of varied, clean speech.")
    if not rows:
        raise SystemExit("No usable speech segments detected. Try a different recording or lower --min-seconds.")

if __name__ == "__main__":
    main()
