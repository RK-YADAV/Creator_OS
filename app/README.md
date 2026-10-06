# I-PostPilot web MVP

Runnable FastAPI MVP: uploads video/transcript, processes transcript windows in a background worker, persists jobs/proposals/feedback in SQLite, exports Markdown, and renders approved windows with ffmpeg. SQLite and filesystem artifacts are intentional for this evaluation phase. A deterministic fallback remains available for UI development, but it must not be used to claim model performance.

## JarvisLabs/Ubuntu

For a repeatable GPU installation, run the staged installer. It installs the base app,
CUDA-enabled PyTorch, GPU packages, validates the VM, and downloads the core models:

```bash
cd CreatorOS-Final_Capstone_100x
bash app/setup_jarvislabs.sh
```

Before installing, check the VM and select a persistent disk for the model cache:

```bash
nvidia-smi
python3 --version
df -h
free -h
ffmpeg -version
ffmpeg -encoders | grep -E 'nvenc|264'
```

The installer defaults to `model-cache/` in the repository. For a persistent mounted
volume, set `IPOSTPILOT_MODEL_DIR=/path/to/persistent/model-cache` first. Core models
can also be installed individually to control GPU credits:

```bash
source .venv/bin/activate
python app/download_models.py --asr
python app/download_models.py --embeddings --reranker --vad
```

The optional diarization model is gated by Hugging Face. Accept its terms on the model
pages, configure the token directly on the VM (never paste it into chat), then run:

```bash
export HF_TOKEN=...                 # configure in the VM secret/environment store
python app/download_models.py --diarization
```

Start the service:

```bash
IPOSTPILOT_DATA_DIR="$PWD/runtime-data" \
IPOSTPILOT_MODEL_DIR="$PWD/model-cache" \
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://<jarvislabs-ip>:8000`. Upload `.mp4` and `.txt`/`.json`; JSON may contain `{"segments":[{"start":0,"end":4,"text":"..."}]}`. API docs are at `/docs`.

### Runtime modes

The default is forgiving for local UI development. For an experiment, require real
transcripts or a working local ASR model:

```bash
export IPOSTPILOT_STRICT_MODE=1
export IPOSTPILOT_WHISPER_MODEL=large-v3
export IPOSTPILOT_WHISPER_DEVICE=cuda
export IPOSTPILOT_WHISPER_COMPUTE_TYPE=float16
```

Strict mode raises an explicit error instead of turning missing model output into a
successful-looking deterministic proposal. This keeps evaluation results honest.
When CUDA libraries such as `libcublas.so.12` are unavailable, video-only ASR
defaults to a transparent CPU fallback and reports mode
`faster-whisper-cpu-fallback`. Set `IPOSTPILOT_ASR_CPU_FALLBACK=0` to fail instead
while repairing the GPU environment. CPU fallback is slower but still extracts the
transcript from the uploaded video.

Windows is supported for development (`py -m venv .venv`, `.venv\Scripts\activate`, `py -m uvicorn app.main:app`); use a Windows ffmpeg build for rendering.

## Flow 1 learning path

The first integrated vertical slice is intentionally simple and inspectable:

```text
POST /api/creators
  -> POST /api/creators/{id}/examples  (repeat for approved/rejected video + transcript pairs)
  -> POST /api/creators/{id}/build-profile
  -> GET  /api/creators/{id}            (review generated JSON)
    -> PUT  /api/creators/{id}/profile    (edit persona JSON)
    -> POST /api/creators/{id}/approve-profile
    -> POST /api/jobs with creator_id     (Flow 2 uses the approved profile)
  ```

  The generated profile is saved in SQLite as JSON and Markdown fields. Each historical
  example should include its Short/Reel video and transcript. The current profile learns
  transparent baseline signals: explicit preferences, recurring terms from approved
  transcripts, approved/rejected example counts, preferred clip duration, and basic
  video metadata such as example count and duration. It also exposes an editable persona
  section for voice, storytelling, caption, and brand defaults. Candidate windows are
  merged toward sentence boundaries and receive a narrative-completeness score.
  The profile must be approved before it can influence candidate ranking.

  Rendered proposals are portrait 9:16 clips by default with burned-in captions. Caption
  files are also available through:

  ```text
  GET /api/proposals/{id}/captions.srt
  GET /api/proposals/{id}/captions.vtt
  POST /api/proposals/{id}/render
  ```

  The renderer uses normalized, audio-preserving media and stores word-level ASR timing
  when Faster-Whisper provides it. The current style controls are transparent defaults;
  learned CLIP/SigLIP embeddings, OCR, and advanced face tracking remain future upgrades.

This is the first teaching slice, not the final intelligence layer. The next steps
are editable profile review, source-video/example pairing, word-level ASR, richer
features, and evaluation against a generic ranking baseline.
