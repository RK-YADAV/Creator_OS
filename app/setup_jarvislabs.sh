#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

sudo apt-get update
sudo apt-get install -y ffmpeg python3-venv build-essential
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r app/requirements.txt

# Adjust cu128 only if the VM's NVIDIA driver does not support it.
python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r app/requirements-gpu.txt

export IPOSTPILOT_MODEL_DIR="${IPOSTPILOT_MODEL_DIR:-$ROOT/model-cache}"
mkdir -p "$IPOSTPILOT_MODEL_DIR" "$ROOT/runtime-data"
python app/smoke_test.py
python app/download_models.py --asr --embeddings --reranker --vad

echo
echo "Setup complete. Start with:"
echo "  source .venv/bin/activate"
echo "  IPOSTPILOT_DATA_DIR=$ROOT/runtime-data IPOSTPILOT_MODEL_DIR=$IPOSTPILOT_MODEL_DIR uvicorn app.main:app --host 0.0.0.0 --port 8000"
