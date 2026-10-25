#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW_JSONL="${RAW_JSONL:-$ROOT/data/training/train_raw.jsonl}"
TRAIN_JSONL="${TRAIN_JSONL:-$ROOT/data/training/train_with_codes.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT/model-output/harsh-yadav-qwen3}"
MODEL_ID="${MODEL_ID:-Qwen/Qwen3-TTS-12Hz-0.6B-Base}"
TOKENIZER_ID="${TOKENIZER_ID:-Qwen/Qwen3-TTS-Tokenizer-12Hz}"
DEVICE="${DEVICE:-cuda:0}"
BATCH_SIZE="${BATCH_SIZE:-2}"
LEARNING_RATE="${LEARNING_RATE:-2e-5}"
EPOCHS="${EPOCHS:-3}"
SPEAKER_NAME="${SPEAKER_NAME:-harsh_yadav}"
UPSTREAM_DIR="${UPSTREAM_DIR:-$ROOT/vendor/Qwen3-TTS}"

if [[ ! -f "$RAW_JSONL" ]]; then
  echo "Missing $RAW_JSONL. Prepare recordings, review manifest.csv, then run build_train_jsonl.py."
  exit 2
fi

python - <<'PY'
import torch
if not torch.cuda.is_available():
    raise SystemExit("CUDA GPU not detected. Run this script on a CUDA GPU notebook/runtime, not the Mac CPU.")
print("CUDA GPU:", torch.cuda.get_device_name(0))
PY

if [[ ! -d "$UPSTREAM_DIR/.git" ]]; then
  mkdir -p "$(dirname "$UPSTREAM_DIR")"
  git clone --depth 1 https://github.com/QwenLM/Qwen3-TTS.git "$UPSTREAM_DIR"
else
  git -C "$UPSTREAM_DIR" pull --ff-only
fi

python -m pip install -U qwen-tts
mkdir -p "$(dirname "$TRAIN_JSONL")" "$OUTPUT_DIR"
(
  cd "$UPSTREAM_DIR/finetuning"
  python prepare_data.py \
    --device "$DEVICE" \
    --tokenizer_model_path "$TOKENIZER_ID" \
    --input_jsonl "$RAW_JSONL" \
    --output_jsonl "$TRAIN_JSONL"
  python sft_12hz.py \
    --init_model_path "$MODEL_ID" \
    --output_model_path "$OUTPUT_DIR" \
    --train_jsonl "$TRAIN_JSONL" \
    --batch_size "$BATCH_SIZE" \
    --lr "$LEARNING_RATE" \
    --num_epochs "$EPOCHS" \
    --speaker_name "$SPEAKER_NAME"
)

FINAL_CHECKPOINT="$OUTPUT_DIR/checkpoint-epoch-$((EPOCHS - 1))"
if [[ -d "$FINAL_CHECKPOINT" ]]; then
  printf '\nTraining run finished. Candidate final checkpoint:\n%s\n' "$FINAL_CHECKPOINT"
  printf 'Validate it with the inference script before publishing or using it in projects.\n'
else
  echo "Training command returned, but expected checkpoint was not found: $FINAL_CHECKPOINT"
  echo "Available output:"
  find "$OUTPUT_DIR" -maxdepth 2 -type f | head -80 || true
  exit 3
fi
