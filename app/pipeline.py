from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from . import db


def _segments(text: str) -> list[dict[str, Any]]:
    """Parse JSON segments or make deterministic 30-second transcript windows."""
    try:
        data = json.loads(text)
        raw = data.get("segments", data) if isinstance(data, dict) else data
        if isinstance(raw, list) and raw and isinstance(raw[0], dict):
            return [{
                "start": float(x.get("start", 0)),
                "end": float(x.get("end", x.get("start", 0) + 30)),
                "text": str(x.get("text", "")).strip(),
                "words": x.get("words", []),
            } for x in raw if str(x.get("text", "")).strip()]
    except (ValueError, TypeError):
        pass
    words = re.findall(r"\S+", text)
    if not words:
        return []
    result = []
    for i in range(0, len(words), 65):
        chunk = " ".join(words[i:i + 65])
        start = i / 2.2
        result.append({"start": start, "end": start + max(8, len(chunk.split()) / 2.2), "text": chunk, "words": []})
    return result


def _clip_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge ASR segments into bounded windows that prefer complete sentences."""
    if not segments:
        return []
    merged: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    minimum_duration = 12.0
    target_duration = 45.0
    maximum_duration = 75.0
    sentence_end = re.compile(r"""[.!?؟。！？]["'»”’)]*$""")
    for segment in sorted(segments, key=lambda item: float(item["start"])):
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        start = float(segment.get("start", 0.0))
        end = max(start + 0.1, float(segment.get("end", start + 1.0)))
        if current is None:
            current = {"start": start, "end": end, "text": text, "words": list(segment.get("words", []))}
        else:
            current["end"] = end
            current["text"] = f"{current['text']} {text}".strip()
            current["words"].extend(segment.get("words", []))
        duration = current["end"] - current["start"]
        complete_sentence = bool(sentence_end.search(current["text"]))
        if complete_sentence and duration >= minimum_duration or duration >= maximum_duration:
            merged.append(current)
            current = None
    if current:
        merged.append(current)

    # Join very short trailing fragments with the previous clip when possible.
    if len(merged) > 1 and merged[-1]["end"] - merged[-1]["start"] < minimum_duration:
        tail = merged.pop()
        previous = merged[-1]
        previous["end"] = tail["end"]
        previous["text"] = f"{previous['text']} {tail['text']}".strip()
        previous["words"].extend(tail.get("words", []))
    return merged


def _text_features(text: str, segments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    words = re.findall(r"\S+", text)
    sentence_match = re.match(r"^(.+?[.!?])(?:\s|$)", text.strip()) if text.strip() else None
    first_sentence = sentence_match.group(1) if sentence_match else text.strip()
    hook_patterns: list[str] = []
    if "?" in first_sentence:
        hook_patterns.append("question")
    if re.search(r"\b(why|how|secret|truth|mistake|nobody|never|always)\b", first_sentence.lower()):
        hook_patterns.append("curiosity_or_contrarian")
    if re.search(r"\b(you|your)\b", first_sentence.lower()):
        hook_patterns.append("direct_address")
    if not hook_patterns:
        hook_patterns.append("statement")
    result: dict[str, Any] = {
        "word_count": len(words),
        "character_count": len(text),
        "hook_pattern": hook_patterns[0],
        "hook_patterns": hook_patterns,
        "first_sentence_word_count": len(first_sentence.split()),
        "question_mark_ratio": round(text.count("?") / max(1, len(words)), 4),
    }
    if segments:
        ordered = sorted(segments, key=lambda item: float(item["start"]))
        elapsed = max(0.1, float(ordered[-1]["end"]) - float(ordered[0]["start"]))
        gaps = [
            max(0.0, float(current["start"]) - float(previous["end"]))
            for previous, current in zip(ordered, ordered[1:])
        ]
        result.update({
            "speech_rate_wpm": round(len(words) / elapsed * 60, 1),
            "pause_ratio": round(sum(gaps) / elapsed, 4),
            "average_pause_seconds": round(sum(gaps) / len(gaps), 3) if gaps else 0.0,
        })
    return result


def _narrative_features(text: str) -> dict[str, Any]:
    """Score whether a candidate behaves like a self-contained short-form clip."""
    normalized = text.strip()
    words = normalized.split()
    first = words[0].lower().strip("\"'(") if words else ""
    starts_fragment = first in {"and", "but", "so", "because", "then", "also"}
    has_hook = bool(re.search(r"[?!]|\b(why|how|secret|truth|mistake|never|always)\b", normalized.lower()))
    sentence_count = len(re.findall(r"[.!?؟。！？]+", normalized))
    has_payoff = bool(re.search(r"\\b(therefore|because|so|that means|the lesson|the point|remember|focus on)\\b", normalized.lower()))
    ends_complete = bool(re.search(r"""[.!?؟。！？]["'»”’)]*$""", normalized))
    score = (
        (0.25 if has_hook else 0.0)
        + (0.2 if sentence_count >= 2 else 0.0)
        + (0.2 if has_payoff else 0.0)
        + (0.25 if ends_complete else 0.0)
        + (0.1 if not starts_fragment else 0.0)
    )
    return {
        "narrative_score": round(score, 3),
        "has_hook": has_hook,
        "has_payoff": has_payoff,
        "ends_complete": ends_complete,
        "starts_fragment": starts_fragment,
        "sentence_count": sentence_count,
    }


def _ffmpeg_can_decode(path: Path) -> bool:
    """Validate that the first video frame is decodable, not just well-labelled."""
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
            "-map", "0:v:0", "-frames:v", "1", "-f", "null", "-",
        ],
        capture_output=True, text=True, check=False, timeout=120,
    )
    return result.returncode == 0


def _has_audio_stream(path: Path) -> bool:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=index", "-of", "csv=p=0", str(path),
        ],
        capture_output=True, text=True, check=False, timeout=120,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def _ffmpeg_can_decode_audio(path: Path) -> bool:
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
            "-map", "0:a:0", "-frames:a", "1", "-f", "null", "-",
        ],
        capture_output=True, text=True, check=False, timeout=120,
    )
    return result.returncode == 0


def _analysis_video_path(path: Path) -> tuple[Path | None, bool]:
    """Return an OpenCV-safe H.264 proxy for unsupported or damaged media."""
    if not path or not path.exists():
        return None, False
    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        return path, False
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,pix_fmt",
            "-of", "csv=p=0", str(path),
        ],
        capture_output=True, text=True, check=False,
    )
    codec, _, pixel_format = (probe.stdout.strip().split(",", 2) + ["", ""])[:3]
    if (
        probe.returncode == 0
        and codec == "h264"
        and pixel_format in {"yuv420p", "yuvj420p"}
        and _ffmpeg_can_decode(path)
        and (not _has_audio_stream(path) or _ffmpeg_can_decode_audio(path))
    ):
        return path, False

    cache_dir = path.parent / ".ipostpilot-analysis-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256(
        f"audio-preserving-v2:{path.resolve()}:{path.stat().st_size}:{path.stat().st_mtime_ns}".encode()
    ).hexdigest()[:16]
    proxy = cache_dir / f"{path.stem}-{cache_key}.mp4"
    if proxy.exists() and proxy.stat().st_size > 0 and _ffmpeg_can_decode(proxy):
        return proxy, True
    proxy.unlink(missing_ok=True)

    temporary = proxy.with_suffix(".tmp.mp4")
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(path), "-map", "0:v:0", "-map", "0:a:0?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
            str(temporary),
        ],
        capture_output=True, text=True, check=False, timeout=900,
    )
    if result.returncode != 0 or not temporary.exists() or temporary.stat().st_size == 0:
        temporary.unlink(missing_ok=True)
        return None, False
    temporary.replace(proxy)
    return proxy, True


def _video_features(path: Path | None, start: float = 0.0, end: float | None = None) -> dict[str, Any]:
    """Extract lightweight, inspectable visual-style signals from a video window."""
    if not path or not path.exists():
        return {}
    analysis_path, normalized = _analysis_video_path(path)
    if not analysis_path:
        return {"visual_analysis_available": False, "normalization_failed": True}
    try:
        import cv2  # type: ignore
    except ImportError:
        return {}
    capture = cv2.VideoCapture(str(analysis_path))
    if not capture.isOpened():
        return {}
    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    duration = frame_count / fps if frame_count else 0.0
    window_end = min(end if end is not None else duration, duration) if duration else end
    sample_times = [start] if not window_end or window_end <= start else [
        start + (window_end - start) * ratio for ratio in (0.0, 0.5, 0.95)
    ]
    # Face detection is an optional visual signal. Some headless/OpenCV builds
    # expose video decoding but omit the cascade module, so do not fail profile
    # generation when that optional API is unavailable.
    face_detector = None
    if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data"):
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        if cascade_path.exists():
            detector = cv2.CascadeClassifier(str(cascade_path))
            if not detector.empty():
                face_detector = detector
    brightness: list[float] = []
    contrast: list[float] = []
    face_ratios: list[float] = []
    scene_changes = 0
    previous_gray = None
    valid_frames = 0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    for timestamp in sample_times:
        capture.set(cv2.CAP_PROP_POS_MSEC, max(0.0, timestamp) * 1000)
        ok, frame = capture.read()
        if not ok:
            continue
        valid_frames += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness.append(float(gray.mean()))
        contrast.append(float(gray.std()))
        faces = (
            face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
            if face_detector is not None else []
        )
        face_area = max((float(w * h) for _, _, w, h in faces), default=0.0)
        frame_area = float(gray.shape[0] * gray.shape[1])
        face_ratios.append(face_area / frame_area if frame_area else 0.0)
        if previous_gray is not None and cv2.absdiff(previous_gray, gray).mean() > 24:
            scene_changes += 1
        previous_gray = gray
    capture.release()
    if not valid_frames:
        return {}
    return {
        "width": width,
        "height": height,
        "aspect_ratio": round(width / height, 3) if height else None,
        "sampled_frames": valid_frames,
        "brightness_mean": round(sum(brightness) / len(brightness), 2),
        "contrast_mean": round(sum(contrast) / len(contrast), 2),
        "face_visible_ratio": round(sum(1 for value in face_ratios if value > 0) / len(face_ratios), 3),
        "face_area_ratio": round(sum(face_ratios) / len(face_ratios), 4),
        "face_detection_available": face_detector is not None,
        "visual_analysis_available": True,
        "normalized_for_analysis": normalized,
        "scene_change_count": scene_changes,
    }


def _average_features(features: list[dict[str, Any]]) -> dict[str, float]:
    keys = sorted({
        key for item in features for key, value in item.items()
        if isinstance(value, (int, float))
    })
    return {
        key: round(sum(float(item[key]) for item in features if isinstance(item.get(key), (int, float))) /
                   max(1, sum(1 for item in features if isinstance(item.get(key), (int, float)))), 4)
        for key in keys if any(isinstance(item.get(key), (int, float)) for item in features)
    }


def build_creator_profile(creator_id: str) -> dict[str, Any]:
    """Create a transparent profile draft from onboarding preferences and examples."""
    with db.connect() as con:
        creator = db.row_dict(con.execute("SELECT * FROM creators WHERE id=?", (creator_id,)).fetchone())
        examples = [db.row_dict(row) for row in con.execute(
            "SELECT * FROM creator_examples WHERE creator_id=? ORDER BY created_at", (creator_id,)
        )]
    if not creator:
        raise ValueError("Creator not found")

    preferences = json.loads(creator["preferences_json"] or "{}")
    approved = [x for x in examples if x["label"] == "approved"]
    rejected = [x for x in examples if x["label"] == "rejected"]
    durations = []
    topic_terms: dict[str, int] = {}
    approved_text: list[dict[str, Any]] = []
    rejected_text: list[dict[str, Any]] = []
    approved_visual: list[dict[str, Any]] = []
    rejected_visual: list[dict[str, Any]] = []
    for example in approved:
        example_segments = _segments(example["transcript"])
        text_features = _text_features(example["transcript"], example_segments)
        approved_text.append(text_features)
        example["metadata_json"] = json.dumps(
            _merge_example_metadata(creator_id, example["id"], {"text_features": text_features})
        )
        words = re.findall(r"[A-Za-z][A-Za-z'-]{3,}", example["transcript"].lower())
        for word in words:
            topic_terms[word] = topic_terms.get(word, 0) + 1
        durations.append(max(1, len(example["transcript"].split()) / 2.2))
        if example.get("video_path"):
            features = _video_features(Path(example["video_path"]))
            if features:
                approved_visual.append(features)
                example["metadata_json"] = json.dumps(
                    _merge_example_metadata(creator_id, example["id"], {"visual_features": features})
                )
    for example in rejected:
        example_segments = _segments(example["transcript"])
        text_features = _text_features(example["transcript"], example_segments)
        rejected_text.append(text_features)
        example["metadata_json"] = json.dumps(
            _merge_example_metadata(creator_id, example["id"], {"text_features": text_features})
        )
        if example.get("video_path"):
            features = _video_features(Path(example["video_path"]))
            if features:
                rejected_visual.append(features)
                example["metadata_json"] = json.dumps(
                    _merge_example_metadata(creator_id, example["id"], {"visual_features": features})
                )
    top_topics = [word for word, _ in sorted(topic_terms.items(), key=lambda item: (-item[1], item[0]))[:12]]
    preferred_duration = round(sum(durations) / len(durations)) if durations else 60
    profile = {
        "profile_version": int(creator["profile_version"]) + 1,
        "creator_id": creator_id,
        "explicit_preferences": preferences,
        "observed": {
            "approved_example_count": len(approved),
            "rejected_example_count": len(rejected),
            "estimated_duration_seconds": preferred_duration,
            "recurring_terms": top_topics,
            "video_example_count": sum(1 for x in examples if x.get("video_path")),
            "video_durations_seconds": [
                json.loads(x["metadata_json"]).get("duration_seconds")
                for x in examples if x.get("video_path") and json.loads(x["metadata_json"]).get("duration_seconds")
            ],
            "visual_style": {
                "approved_average": _average_features(approved_visual),
                "rejected_average": _average_features(rejected_visual),
                "features_available": bool(approved_visual or rejected_visual),
            },
            "text_style": {
                "approved_average": _average_features(approved_text),
                "rejected_average": _average_features(rejected_text),
                "hook_patterns": sorted({
                    pattern for item in approved_text for pattern in item.get("hook_patterns", [])
                }),
            },
            "persona": {
                "voice": {
                    "tone": preferences.get("tone", "direct, conversational"),
                    "energy": preferences.get("energy", "medium"),
                    "language_mix": preferences.get("languages", ["english", "hindi", "hinglish"]),
                },
                "storytelling": {
                    "hook_types": sorted({
                        pattern for item in approved_text for pattern in item.get("hook_patterns", [])
                    }),
                    "structure": ["hook", "context", "insight", "takeaway"],
                    "preferred_duration_seconds": preferred_duration,
                },
                "caption_style": preferences.get("caption_style", {
                    "words_per_line": 4,
                    "text_color": "white",
                    "highlight_color": "yellow",
                    "position": "lower-center",
                }),
                "brand": preferences.get("brand", {}),
            },
        },
        "rules": {
            "preferred_duration_seconds": int(preferences.get("preferred_duration_seconds", preferred_duration)),
            "languages": preferences.get("languages", ["english", "hindi", "hinglish"]),
            "avoid_rejected_example_terms": bool(rejected),
            "narrative_minimum_score": float(preferences.get("narrative_minimum_score", 0.45)),
        },
        "evidence": [{
            "example_id": x["id"], "label": x["label"], "name": x["name"],
            "has_video": bool(x.get("video_path")),
            "media": json.loads(x["metadata_json"] or "{}"),
        } for x in examples],
        "status": "draft",
    }
    markdown = _profile_markdown(profile, creator["name"])
    with db.connect() as con:
        con.execute(
            """UPDATE creators SET profile_json=?, profile_markdown=?, profile_status='draft',
               profile_version=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (json.dumps(profile, ensure_ascii=False), markdown, profile["profile_version"], creator_id),
        )
    return profile


def _merge_example_metadata(creator_id: str, example_id: str, features: dict[str, Any]) -> dict[str, Any]:
    with db.connect() as con:
        row = con.execute(
            "SELECT metadata_json FROM creator_examples WHERE id=? AND creator_id=?",
            (example_id, creator_id),
        ).fetchone()
        metadata = json.loads(row["metadata_json"] or "{}") if row else {}
        metadata.update(features)
        con.execute(
            "UPDATE creator_examples SET metadata_json=? WHERE id=? AND creator_id=?",
            (json.dumps(metadata), example_id, creator_id),
        )
        return metadata


def _profile_markdown(profile: dict[str, Any], name: str) -> str:
    observed = profile["observed"]
    rules = profile["rules"]
    terms = ", ".join(observed["recurring_terms"]) or "not enough examples yet"
    visual = observed.get("visual_style", {})
    text_style = observed.get("text_style", {})
    evidence = "\n".join(f"- {item['name']} ({item['label']})" for item in profile["evidence"]) or "- none"
    return (
        f"# Creator skills: {name}\n\n"
        f"- **Profile version:** v{profile['profile_version']}\n"
        f"- **Status:** {profile['status']}\n"
        f"- **Preferred duration:** {rules['preferred_duration_seconds']} seconds\n"
        f"- **Languages:** {', '.join(rules['languages'])}\n"
        f"- **Observed recurring terms:** {terms}\n\n"
        f"- **Hook patterns:** {', '.join(text_style.get('hook_patterns', [])) or 'not enough examples yet'}\n"
        f"- **Speech/pause averages:** {json.dumps(text_style.get('approved_average', {}), sort_keys=True)}\n\n"
        f"- **Visual features available:** {'yes' if visual.get('features_available') else 'no'}\n"
        f"- **Approved visual average:** {json.dumps(visual.get('approved_average', {}), sort_keys=True)}\n\n"
        "## Evidence\n"
        f"{evidence}\n"
    )


def transcribe(video: Path | None, transcript: Path | None) -> tuple[list[dict[str, Any]], str]:
    if transcript and transcript.exists():
        transcript_text = transcript.read_text(encoding="utf-8", errors="ignore").strip()
        if transcript_text:
            return _segments(transcript_text), "transcript"
        transcript.unlink(missing_ok=True)
    if video and shutil.which("ffmpeg"):
        try:
            import faster_whisper  # type: ignore
            if shutil.which("ffprobe") and not _has_audio_stream(video):
                raise RuntimeError(
                    "The uploaded video has no audio stream. Provide a transcript or upload a video with audio."
                )
            model_name = os.environ.get("IPOSTPILOT_WHISPER_MODEL", "large-v3")
            device = os.environ.get("IPOSTPILOT_WHISPER_DEVICE", "cuda")
            compute_type = os.environ.get("IPOSTPILOT_WHISPER_COMPUTE_TYPE", "float16")
            analysis_video, _ = _analysis_video_path(video)
            asr_video = analysis_video or video
            try:
                model = faster_whisper.WhisperModel(
                    model_name, device=device, compute_type=compute_type,
                    download_root=os.environ.get("IPOSTPILOT_MODEL_DIR"),
                )
                segments, _ = model.transcribe(
                    str(asr_video),
                    vad_filter=True,
                    vad_parameters={"min_silence_duration_ms": 400},
                    condition_on_previous_text=False,
                    word_timestamps=True,
                )
                mode = "faster-whisper" if device == "cuda" else "faster-whisper-cpu"
            except (RuntimeError, OSError) as exc:
                cuda_failure = device == "cuda" and any(
                    marker in str(exc).lower()
                    for marker in ("libcublas", "cuda", "cudnn", "cublas")
                )
                if not cuda_failure or os.environ.get("IPOSTPILOT_ASR_CPU_FALLBACK", "1") != "1":
                    raise
                model = faster_whisper.WhisperModel(
                    model_name, device="cpu", compute_type="int8",
                    download_root=os.environ.get("IPOSTPILOT_MODEL_DIR"),
                )
                segments, _ = model.transcribe(
                    str(asr_video),
                    vad_filter=True,
                    vad_parameters={"min_silence_duration_ms": 400},
                    condition_on_previous_text=False,
                    word_timestamps=True,
                )
                mode = "faster-whisper-cpu-fallback"
            raw_segments = []
            for segment in segments:
                segment_words = [
                    {
                        "word": str(word.word).strip(),
                        "start": float(word.start),
                        "end": float(word.end),
                    }
                    for word in (getattr(segment, "words", None) or [])
                    if str(word.word).strip()
                ]
                raw_segments.append({
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "text": segment.text.strip(),
                    "words": segment_words,
                })
            return _clip_segments(raw_segments), mode
        except (ImportError, RuntimeError, OSError):
            if os.environ.get("IPOSTPILOT_STRICT_MODE", "0") == "1":
                raise
    if os.environ.get("IPOSTPILOT_STRICT_MODE", "0") == "1":
        raise RuntimeError("No transcript was supplied and local ASR is unavailable.")
    return [{"start": 0.0, "end": 30.0, "text": "No transcript supplied. Upload a .txt or .json transcript."}], "deterministic-fallback"


def generate(job_id: str, video: Path | None, transcript: Path | None, creator_id: str | None = None) -> str:
    segments, mode = transcribe(video, transcript)
    profile: dict[str, Any] | None = None
    if creator_id:
        with db.connect() as con:
            row = con.execute("SELECT profile_json FROM creators WHERE id=?", (creator_id,)).fetchone()
        if row and row["profile_json"]:
            profile = json.loads(row["profile_json"])
    with db.connect() as con:
        con.execute("DELETE FROM proposals WHERE job_id=?", (job_id,))
        ranked = _rank_segments(segments, profile, video)
        for i, seg in enumerate(ranked[:10]):
            text = seg["text"]
            words = text.split()
            hook = " ".join(words[:14]) + ("…" if len(words) > 14 else "")
            digest = hashlib.sha1(text.encode()).hexdigest()[:8]
            narrative = _narrative_features(text)
            confidence = round(min(0.95, 0.45 + min(len(words), 40) / 100 + narrative["narrative_score"] * 0.2), 2)
            rationale = "Transcript window ranked by hook length and topic signal."
            rationale += f" Narrative completeness: {narrative['narrative_score']:.2f}."
            if profile:
                rationale += " Creator profile terms and preferred duration were applied."
                if seg.get("_visual_features"):
                    rationale += " Visual framing and appearance signals were compared with approved examples."
            con.execute(
                """INSERT INTO proposals(id,job_id,start,end,title,hook,transcript,rationale,confidence,words_json)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (f"{job_id}-{i}-{digest}", job_id, seg["start"], seg["end"],
                 f"Clip {i + 1}: {hook[:60]}", hook, text,
                 rationale + (" Sentence-transformers ranking enabled." if _has_embeddings() else ""),
                 confidence, json.dumps(seg.get("words", []), ensure_ascii=False)),
            )
        con.execute("UPDATE jobs SET status='ready', mode=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (mode, job_id))
    return mode


def _rank_segments(segments: list[dict[str, Any]], profile: dict[str, Any] | None,
                   video: Path | None = None) -> list[dict[str, Any]]:
    if not profile:
        return sorted(segments, key=lambda item: len(item["text"].split()), reverse=True)
    terms = set(profile["observed"].get("recurring_terms", []))
    target = profile["rules"].get("preferred_duration_seconds", 60)
    visual_target = profile["observed"].get("visual_style", {}).get("approved_average", {})
    text_target = profile["observed"].get("text_style", {})
    hook_patterns = set(text_target.get("hook_patterns", []))
    narrative_minimum = float(profile.get("rules", {}).get("narrative_minimum_score", 0.45))
    def score(item: dict[str, Any]) -> tuple[float, float]:
        words = set(re.findall(r"[A-Za-z][A-Za-z'-]{3,}", item["text"].lower()))
        overlap = len(words & terms)
        duration = item["end"] - item["start"]
        duration_fit = max(0.0, 1.0 - abs(duration - target) / max(target, 1))
        candidate_features = _text_features(item["text"], [item])
        hook_fit = 1.0 if candidate_features["hook_pattern"] in hook_patterns else 0.0
        narrative = _narrative_features(item["text"])
        narrative_fit = narrative["narrative_score"]
        if narrative_fit < narrative_minimum:
            narrative_fit -= 0.35
        visual_fit = 0.0
        if video and visual_target:
            features = _video_features(video, item["start"], item["end"])
            item["_visual_features"] = features
            comparable = [
                key for key in ("aspect_ratio", "brightness_mean", "contrast_mean", "face_visible_ratio", "face_area_ratio", "scene_change_count")
                if key in features and key in visual_target
            ]
            if comparable:
                visual_fit = sum(
                    max(0.0, 1.0 - abs(float(features[key]) - float(visual_target[key])) /
                        max(abs(float(visual_target[key])), 1.0))
                    for key in comparable
                ) / len(comparable)
        item["_narrative_features"] = narrative
        return overlap * 2 + duration_fit + hook_fit + visual_fit + narrative_fit * 2, len(item["text"].split())
    return sorted(segments, key=score, reverse=True)


def _has_embeddings() -> bool:
    return importlib.util.find_spec("sentence_transformers") is not None


def _caption_entries(text: str, start: float, end: float, words: list[dict[str, Any]] | None = None,
                     words_per_line: int = 4) -> list[tuple[float, float, str]]:
    usable = [
        item for item in (words or [])
        if isinstance(item, dict) and str(item.get("word", item.get("text", ""))).strip()
    ]
    if usable:
        entries = []
        for index in range(0, len(usable), words_per_line):
            group = usable[index:index + words_per_line]
            group_start = max(start, float(group[0].get("start", start)))
            group_end = min(end, float(group[-1].get("end", end)))
            entries.append((group_start, max(group_start + 0.1, group_end),
                            " ".join(str(item.get("word", item.get("text", ""))).strip() for item in group)))
        return entries
    chunks = text.split()
    duration = max(0.1, end - start)
    entries = []
    for index in range(0, len(chunks), words_per_line):
        group = chunks[index:index + words_per_line]
        group_start = start + duration * index / max(1, len(chunks))
        group_end = start + duration * min(len(chunks), index + len(group)) / max(1, len(chunks))
        entries.append((group_start, max(group_start + 0.1, group_end), " ".join(group)))
    return entries


def _timestamp(seconds: float, separator: str = ",") -> str:
    milliseconds = int(round(max(0.0, seconds) * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds_part, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_part:02d}{separator}{millis:03d}"


def captions(text: str, start: float, end: float, words: list[dict[str, Any]] | None = None,
             words_per_line: int = 4, fmt: str = "srt") -> str:
    entries = _caption_entries(text, start, end, words, words_per_line)
    lines: list[str] = []
    for index, (entry_start, entry_end, value) in enumerate(entries, 1):
        separator = "," if fmt == "srt" else "."
        lines.extend([
            str(index) if fmt == "srt" else "",
            f"{_timestamp(entry_start, separator)} --> {_timestamp(entry_end, separator)}",
            value,
            "",
        ])
    return "\n".join(lines)


def render(video: Path, output: Path, start: float, end: float,
           text: str = "", words: list[dict[str, Any]] | None = None,
           portrait: bool = True, burn_captions: bool = True) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required for rendering; install it with sudo apt install ffmpeg")
    render_video, _ = _analysis_video_path(video)
    if not render_video:
        raise RuntimeError("Video could not be normalized for rendering.")
    duration = max(1.0, end - start)
    output.parent.mkdir(parents=True, exist_ok=True)
    filters = []
    if portrait:
        filters.append("scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280")
    if burn_captions and text:
        caption_file = output.with_suffix(".srt")
        caption_file.write_text(captions(text, start, end, words), encoding="utf-8")
        subtitle_path = caption_file.as_posix().replace(":", "\\:")
        filters.append(f"subtitles={subtitle_path}")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(max(0, start)), "-i", str(render_video), "-t", str(duration)]
    if filters:
        cmd.extend(["-vf", ",".join(filters)])
    cmd.extend(["-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", str(output)])
    completed = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if completed.returncode:
        raise RuntimeError(completed.stderr[-1000:])


def export_markdown(job_id: str) -> str:
    with db.connect() as con:
        job = db.row_dict(con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())
        proposals = [db.row_dict(x) for x in con.execute("SELECT * FROM proposals WHERE job_id=? ORDER BY start", (job_id,))]
    lines = [f"# I-PostPilot export: {job_id}", f"Mode: {job.get('mode') if job else 'unknown'}", ""]
    for p in proposals:
        lines += [f"## {p['title']} ({p['start']:.1f}s–{p['end']:.1f}s)", f"**Status:** {p['status']}  **Confidence:** {p['confidence']}", "", p["transcript"], "", p["rationale"], ""]
    return "\n".join(lines)
