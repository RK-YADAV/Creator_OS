"""Validate the JarvisLabs runtime without processing a full video."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys


def check(label: str, passed: bool, detail: str = "") -> None:
    print(f"[{'PASS' if passed else 'FAIL'}] {label}{': ' + detail if detail else ''}")
    if not passed:
        raise SystemExit(1)


def main() -> None:
    check("Python", sys.version_info >= (3, 10), sys.version.split()[0])
    check("FFmpeg", shutil.which("ffmpeg") is not None, shutil.which("ffmpeg") or "not found")
    check("ffprobe", shutil.which("ffprobe") is not None, shutil.which("ffprobe") or "not found")
    try:
        import torch
        check("PyTorch import", True, torch.__version__)
        check("CUDA available", torch.cuda.is_available(), str(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "false"))
    except ImportError:
        check("PyTorch import", False, "install a CUDA-enabled torch build")
    for package in ("faster_whisper", "sentence_transformers", "silero_vad"):
        check(package, importlib.util.find_spec(package) is not None, "importable")
    if os.environ.get("HF_TOKEN"):
        print("[INFO] HF_TOKEN is configured; pyannote can be enabled after model terms are accepted.")
    else:
        print("[INFO] HF_TOKEN is not configured; skipping gated diarization.")
    print("Runtime smoke test passed.")


if __name__ == "__main__":
    main()
