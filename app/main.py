from __future__ import annotations

import json
import logging
import subprocess
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import db, pipeline

app = FastAPI(title="I-PostPilot MVP", version="1.0")
BASE = Path(__file__).resolve().parent
UPLOADS = Path(__import__("os").environ.get("IPOSTPILOT_UPLOAD_DIR", str(BASE / "data" / "uploads")))
UPLOADS.mkdir(parents=True, exist_ok=True)
executor = ThreadPoolExecutor(max_workers=2)
logger = logging.getLogger(__name__)
db.init_db()


@app.get("/", response_class=HTMLResponse)
def index() -> FileResponse:
    return FileResponse(BASE / "static" / "index.html")


def save_upload(upload: UploadFile | None, destination: Path) -> Path | None:
    if not upload or not upload.filename:
        return None
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / Path(upload.filename or "upload").name
    with path.open("wb") as out:
        shutil.copyfileobj(upload.file, out)
    return path


def media_metadata(path: Path | None) -> dict:
    if not path or not path.exists():
        return {}
    metadata = {"filename": path.name, "size_bytes": path.stat().st_size}
    if shutil.which("ffprobe"):
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                metadata["duration_seconds"] = round(float(result.stdout.strip()), 3)
            except ValueError:
                pass
    return metadata


def run_job(job_id: str, video_path: Path | None, transcript_path: Path | None, creator_id: str | None) -> None:
    """Run a background job and persist failures instead of leaving it processing forever."""
    try:
        pipeline.generate(job_id, video_path, transcript_path, creator_id)
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        with db.connect() as con:
            con.execute(
                "UPDATE jobs SET status='failed', error=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (str(exc) or exc.__class__.__name__, job_id),
            )


@app.post("/api/creators")
def create_creator(name: str = Form(...), preferences: str = Form("{}")) -> dict:
    try:
        parsed = json.loads(preferences)
        if not isinstance(parsed, dict):
            raise ValueError
    except ValueError as exc:
        raise HTTPException(400, "preferences must be a JSON object") from exc
    creator_id = uuid.uuid4().hex
    with db.connect() as con:
        con.execute("INSERT INTO creators(id,name,preferences_json) VALUES(?,?,?)",
                    (creator_id, name.strip(), json.dumps(parsed, ensure_ascii=False)))
    return {"id": creator_id, "name": name.strip(), "profile_status": "draft"}


@app.post("/api/creators/{creator_id}/examples")
def add_creator_example(
    creator_id: str,
    transcript: UploadFile = File(...),
    video: UploadFile | None = File(None),
    label: str = Form("approved"),
    name: str | None = Form(None),
) -> dict:
    if label not in {"approved", "rejected"}:
        raise HTTPException(400, "label must be approved or rejected")
    text = transcript.file.read().decode("utf-8", errors="ignore").strip()
    if not text:
        raise HTTPException(400, "Example transcript is empty")
    example_id = uuid.uuid4().hex
    folder = UPLOADS / "creators" / creator_id / "examples" / example_id
    video_path = save_upload(video, folder)
    metadata = media_metadata(video_path)
    with db.connect() as con:
        if not con.execute("SELECT 1 FROM creators WHERE id=?", (creator_id,)).fetchone():
            raise HTTPException(404, "Creator not found")
        con.execute(
            "INSERT INTO creator_examples(id,creator_id,name,transcript,video_path,label,metadata_json) VALUES(?,?,?,?,?,?,?)",
            (example_id, creator_id, name or transcript.filename or "example", text,
             str(video_path) if video_path else None, label, json.dumps(metadata)),
        )
    return {"id": example_id, "creator_id": creator_id, "label": label,
            "video_uploaded": video_path is not None, "metadata": metadata}


@app.post("/api/creators/{creator_id}/build-profile")
def build_profile(creator_id: str) -> dict:
    try:
        profile = pipeline.build_creator_profile(creator_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:
        logger.exception("Profile build failed for creator %s", creator_id)
        raise HTTPException(
            500,
            "Profile build failed. Check the Uvicorn terminal for the traceback.",
        ) from exc
    return profile


@app.get("/api/creators/{creator_id}")
def get_creator(creator_id: str) -> dict:
    with db.connect() as con:
        creator = db.row_dict(con.execute("SELECT * FROM creators WHERE id=?", (creator_id,)).fetchone())
        if not creator:
            raise HTTPException(404, "Creator not found")
        creator["preferences"] = json.loads(creator.pop("preferences_json") or "{}")
        creator["profile"] = json.loads(creator.pop("profile_json") or "null")
        creator["examples"] = [dict(x) for x in con.execute(
            "SELECT id,name,label,video_path,metadata_json,created_at FROM creator_examples WHERE creator_id=? ORDER BY created_at",
            (creator_id,),
        )]
        for example in creator["examples"]:
            example["has_video"] = bool(example.pop("video_path"))
            example["metadata"] = json.loads(example.pop("metadata_json") or "{}")
    return creator


@app.post("/api/creators/{creator_id}/approve-profile")
def approve_profile(creator_id: str) -> dict:
    with db.connect() as con:
        updated = con.execute(
            "UPDATE creators SET profile_status='approved', updated_at=CURRENT_TIMESTAMP WHERE id=? AND profile_json IS NOT NULL",
            (creator_id,),
        ).rowcount
    if not updated:
        raise HTTPException(400, "Build a profile before approving it")
    return {"creator_id": creator_id, "profile_status": "approved"}


@app.put("/api/creators/{creator_id}/profile")
def update_profile(creator_id: str, profile: str = Form(...)) -> dict:
    try:
        parsed = json.loads(profile)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "profile must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(400, "profile must be a JSON object")
    with db.connect() as con:
        creator = con.execute("SELECT id FROM creators WHERE id=?", (creator_id,)).fetchone()
        if not creator:
            raise HTTPException(404, "Creator not found")
        con.execute(
            "UPDATE creators SET profile_json=?, profile_status='draft', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(parsed, ensure_ascii=False), creator_id),
        )
    return {"creator_id": creator_id, "profile_status": "draft", "profile": parsed}


@app.post("/api/jobs")
def create_job(background: BackgroundTasks, video: UploadFile | None = File(None), transcript: UploadFile | None = File(None),
               transcript_text: str | None = Form(None), creator_id: str | None = Form(None)) -> dict:
    job_id = uuid.uuid4().hex
    folder = UPLOADS / job_id
    video_path = save_upload(video, folder)
    transcript_path = save_upload(transcript, folder)
    if transcript_text:
        transcript_path = folder / "transcript.txt"
        folder.mkdir(parents=True, exist_ok=True)
        transcript_path.write_text(transcript_text, encoding="utf-8")
    if not video_path and not transcript_path:
        raise HTTPException(400, "Upload a video or transcript")
    if creator_id:
        with db.connect() as con:
            creator = con.execute(
                "SELECT id FROM creators WHERE id=? AND profile_status='approved'", (creator_id,)
            ).fetchone()
        if not creator:
            raise HTTPException(400, "creator_id must reference an approved creator profile")
    with db.connect() as con:
        con.execute("INSERT INTO jobs(id,status,video_path,transcript_path,creator_id) VALUES(?,?,?,?,?)",
                    (job_id, "processing", str(video_path) if video_path else None, str(transcript_path) if transcript_path else None,
                     creator_id))
    background.add_task(executor.submit, run_job, job_id, video_path, transcript_path, creator_id)
    return {"id": job_id, "status": "processing"}


@app.get("/api/jobs")
def jobs() -> list[dict]:
    with db.connect() as con:
        return [dict(x) for x in con.execute("SELECT * FROM jobs ORDER BY created_at DESC")]


@app.get("/api/jobs/{job_id}")
def job(job_id: str) -> dict:
    with db.connect() as con:
        item = db.row_dict(con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())
        if not item:
            raise HTTPException(404, "Job not found")
        item["proposals"] = [dict(x) for x in con.execute("SELECT * FROM proposals WHERE job_id=? ORDER BY start", (job_id,))]
    return item


@app.post("/api/proposals/{proposal_id}/feedback")
def feedback(proposal_id: str, action: str = Form(...), feedback: str = Form(""), edited: str = Form("")) -> dict:
    if action not in {"approve", "reject", "edit"}:
        raise HTTPException(400, "action must be approve, reject, or edit")
    with db.connect() as con:
        exists = con.execute("SELECT 1 FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if not exists:
            raise HTTPException(404, "Proposal not found")
        con.execute("INSERT INTO feedback(proposal_id,action,feedback,edited_json) VALUES(?,?,?,?)",
                    (proposal_id, action, feedback, edited or None))
        con.execute("UPDATE proposals SET status=?, edited_json=? WHERE id=?", (action, edited or None, proposal_id))
    return {"ok": True, "proposal_id": proposal_id, "action": action}


@app.get("/api/proposals/{proposal_id}/captions.{fmt}")
def proposal_captions(proposal_id: str, fmt: str) -> PlainTextResponse:
    if fmt not in {"srt", "vtt"}:
        raise HTTPException(400, "Caption format must be srt or vtt")
    with db.connect() as con:
        proposal = db.row_dict(con.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone())
    if not proposal:
        raise HTTPException(404, "Proposal not found")
    words = json.loads(proposal.get("words_json") or "[]")
    body = pipeline.captions(proposal["transcript"], proposal["start"], proposal["end"], words, fmt=fmt)
    media_type = "text/vtt" if fmt == "vtt" else "application/x-subrip"
    return PlainTextResponse(body, media_type=media_type,
                             headers={"Content-Disposition": f'attachment; filename="{proposal_id}.{fmt}"'})


@app.post("/api/proposals/{proposal_id}/render")
def render(proposal_id: str, portrait: bool = Form(True), burn_captions: bool = Form(True)) -> FileResponse:
    with db.connect() as con:
        p = db.row_dict(con.execute("SELECT p.*,j.video_path FROM proposals p JOIN jobs j ON j.id=p.job_id WHERE p.id=?", (proposal_id,)).fetchone())
    if not p or not p["video_path"]:
        raise HTTPException(404, "Proposal or source video not found")
    output = UPLOADS / p["job_id"] / f"{proposal_id}.mp4"
    try:
        pipeline.render(
            Path(p["video_path"]), output, p["start"], p["end"],
            text=p["transcript"], words=json.loads(p.get("words_json") or "[]"),
            portrait=portrait, burn_captions=burn_captions,
        )
    except (RuntimeError, OSError) as exc:
        raise HTTPException(503, str(exc))
    return FileResponse(output, media_type="video/mp4", filename=output.name)


@app.get("/api/jobs/{job_id}/export.md")
def export_md(job_id: str) -> PlainTextResponse:
    return PlainTextResponse(pipeline.export_markdown(job_id), media_type="text/markdown",
                             headers={"Content-Disposition": f'attachment; filename="{job_id}.md"'})


app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
