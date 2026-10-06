"""Download and validate the local models used by the I-PostPilot pipeline.

Run this from the repository root after installing requirements-gpu.txt:
    python app/download_models.py --asr --embeddings --reranker --vad

Models are cached in IPOSTPILOT_MODEL_DIR, defaulting to ~/.cache/ipostpilot.
The diarization model is deliberately opt-in because it is gated on Hugging Face.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


MODEL_DIR = Path(os.environ.get("IPOSTPILOT_MODEL_DIR", Path.home() / ".cache" / "ipostpilot"))
ASR_MODEL = os.environ.get("IPOSTPILOT_WHISPER_MODEL", "large-v3")
EMBEDDING_MODEL = os.environ.get("IPOSTPILOT_EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
RERANKER_MODEL = os.environ.get("IPOSTPILOT_RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")


def download_asr() -> None:
    from faster_whisper import WhisperModel

    path = MODEL_DIR / "faster-whisper"
    print(f"Downloading/checking ASR model: {ASR_MODEL}")
    WhisperModel(ASR_MODEL, device="cpu", compute_type="int8", download_root=str(path))
    print(f"ASR ready: {path}")


def download_embeddings() -> None:
    from sentence_transformers import SentenceTransformer

    print(f"Downloading/checking embedding model: {EMBEDDING_MODEL}")
    SentenceTransformer(EMBEDDING_MODEL, cache_folder=str(MODEL_DIR / "huggingface"))
    print("Embeddings ready")


def download_reranker() -> None:
    from sentence_transformers import CrossEncoder

    print(f"Downloading/checking reranker model: {RERANKER_MODEL}")
    CrossEncoder(RERANKER_MODEL, cache_folder=str(MODEL_DIR / "huggingface"))
    print("Reranker ready")


def check_vad() -> None:
    import torch
    from silero_vad import load_silero_vad

    print("Downloading/checking Silero VAD")
    load_silero_vad(onnx=False)
    print(f"VAD ready (torch {torch.__version__})")


def download_diarization() -> None:
    from pyannote.audio import Pipeline

    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("Set HF_TOKEN before downloading the gated diarization model.")
    print("Downloading/checking pyannote speaker diarization")
    Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", token=token)
    print("Diarization ready")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asr", action="store_true")
    parser.add_argument("--embeddings", action="store_true")
    parser.add_argument("--reranker", action="store_true")
    parser.add_argument("--vad", action="store_true")
    parser.add_argument("--diarization", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        parser.error("Select at least one model flag.")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if args.asr:
        download_asr()
    if args.embeddings:
        download_embeddings()
    if args.reranker:
        download_reranker()
    if args.vad:
        check_vad()
    if args.diarization:
        download_diarization()
    print(f"All requested models are ready. Cache: {MODEL_DIR}")


if __name__ == "__main__":
    main()
