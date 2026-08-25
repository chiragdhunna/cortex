"""REST API for Cortex jobs."""
from hashlib import sha256
from pathlib import Path
import shutil
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from core.config import settings
from core.database import get_session, init_database
from core.models import Artifact, Job, NotesResult
from jobs.tasks import run_format, run_generation, run_pipeline
from core.validation import validate_media_duration

app = FastAPI(title="Cortex")

@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight liveness response for Compose and browser checks."""
    return {"status": "ok"}

@app.on_event("startup")
def startup() -> None:
    """Initialize persistence and storage before serving requests."""
    settings.storage_dir.mkdir(parents=True, exist_ok=True); init_database()

class LinkJobRequest(BaseModel):
    """JSON submission body for an audio or video link."""
    url: str
    source_type: str = "video_link"
    category: str
    formats: list[str] = Field(default_factory=lambda: ["markdown"])
    provider: str | None = None

class RegenerateRequest(BaseModel):
    """Generation-only job update request."""
    category: str
    provider: str | None = None

class FormatRequest(BaseModel):
    """Format-only job update request."""
    formats: list[str]

def _create_job(db: Session, source_type: str, source_ref: str, source_hash: str, category: str, formats: list[str], provider: str | None) -> Job:
    """Persist a queued job with validated category and output requests."""
    from core.categories.registry import get_category_model
    from formatters.registry import registered_formats
    import formatters  # noqa: F401
    get_category_model(category)
    if not formats or set(formats) - registered_formats(): raise HTTPException(422, "Unsupported or empty formats")
    job = Job(source_type=source_type, source_ref=source_ref, source_hash=source_hash, category=category, formats=formats, provider=provider)
    db.add(job); db.commit(); db.refresh(job)
    return job

@app.post("/jobs")
def submit_link(request: LinkJobRequest, db: Session = Depends(get_session)) -> dict[str, str]:
    """Submit a link job and enqueue the full background pipeline."""
    if request.source_type not in {"video_link", "audio_link"}: raise HTTPException(422, "Invalid link source type")
    job = _create_job(db, request.source_type, request.url, sha256(request.url.encode()).hexdigest(), request.category, request.formats, request.provider)
    run_pipeline.delay(job.id)
    return {"job_id": job.id}

@app.post("/jobs/upload")
def submit_upload(file: UploadFile = File(...), category: str = Form(...), formats: list[str] = Form(...), provider: str | None = Form(None), db: Session = Depends(get_session)) -> dict[str, str]:
    """Store an uploaded PDF/audio/video then enqueue a pipeline job."""
    extension = Path(file.filename or "").suffix.lower()
    kind = "pdf" if extension == ".pdf" else "audio" if extension in {".mp3", ".wav", ".m4a"} else "video" if extension in {".mp4", ".mov"} else None
    if not kind: raise HTTPException(422, "Unsupported file type")
    content = file.file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024: raise HTTPException(413, "File exceeds configured size limit")
    digest = sha256(content).hexdigest(); destination = settings.storage_dir / "uploads" / f"{digest}{extension}"; destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(content)
    if kind in {"audio", "video"}:
        try: validate_media_duration(destination, settings.max_duration_seconds)
        except ValueError as exc: destination.unlink(missing_ok=True); raise HTTPException(422, str(exc)) from exc
    job = _create_job(db, kind, str(destination), digest, category, formats, provider)
    run_pipeline.delay(job.id)
    return {"job_id": job.id}

@app.get("/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_session)) -> dict:
    """Return status and progress metadata for polling clients."""
    job = db.get(Job, job_id)
    if not job: raise HTTPException(404, "Job not found")
    return {"id":job.id, "status":job.status, "stage":job.stage, "error":job.error, "category":job.category, "formats":job.formats}

@app.get("/jobs")
def list_jobs(db: Session = Depends(get_session)) -> list[dict]:
    """Return persisted local job history, newest first."""
    jobs = db.scalars(select(Job).order_by(Job.created_at.desc())).all()
    return [{"id": job.id, "status": job.status, "stage": job.stage, "category": job.category, "formats": job.formats} for job in jobs]

@app.get("/jobs/{job_id}/result")
def get_result(job_id: str, db: Session = Depends(get_session)) -> dict:
    """Return validated canonical notes after generation."""
    job = db.get(Job, job_id)
    if not job or not job.notes_result_id: raise HTTPException(404, "Result not available")
    return db.get(NotesResult, job.notes_result_id).canonical_json

@app.get("/jobs/{job_id}/download")
def download(job_id: str, format: str, db: Session = Depends(get_session)) -> FileResponse:
    """Stream an existing rendered artifact."""
    artifact = db.scalar(select(Artifact).where(Artifact.job_id == job_id, Artifact.format == format).order_by(Artifact.created_at.desc()))
    if not artifact: raise HTTPException(404, "Artifact not available")
    return FileResponse(artifact.path, media_type=artifact.content_type, filename=Path(artifact.path).name)

@app.post("/jobs/{job_id}/regenerate")
def regenerate(job_id: str, request: RegenerateRequest, db: Session = Depends(get_session)) -> dict[str, str]:
    """Enqueue generation against stored transcript, explicitly skipping ingestion."""
    job = db.get(Job, job_id)
    if not job or not job.transcript_id: raise HTTPException(404, "Transcript not available")
    run_generation.delay(job_id, request.category, request.provider)
    return {"job_id": job_id}

@app.post("/jobs/{job_id}/format")
def add_format(job_id: str, request: FormatRequest, db: Session = Depends(get_session)) -> dict[str, str]:
    """Enqueue formatting against canonical notes, explicitly skipping generation."""
    job = db.get(Job, job_id)
    if not job or not job.notes_result_id: raise HTTPException(404, "Notes result not available")
    run_format.delay(job_id, request.formats)
    return {"job_id": job_id}
