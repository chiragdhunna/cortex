"""Celery tasks composing ingestion, generation, and formatting stages."""
from hashlib import sha256
from pathlib import Path
from sqlalchemy import select
from core.config import settings
from core.database import SessionLocal
from core.models import Artifact, Job, NotesResult, Transcript
from core.llm.factory import get_provider
from core.notes_generator import generate_notes
from formatters.registry import render_format
import formatters  # noqa: F401
from ingestion.pdf_extractor import extract_pdf
from ingestion.transcriber import transcribe_media
from ingestion.link_resolver import resolve_link
from jobs.celery_app import celery_app


def _transition(job: Job, status: str, stage: str, error: str | None = None) -> None:
    """Set an observable pipeline state on a job."""
    job.status, job.stage, job.error = status, stage, error


def ingest_job(job_id: str) -> None:
    """Perform only ingestion and persist the normalized transcript."""
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        if not job: raise ValueError("Job not found")
        _transition(job, "transcribing", "ingestion")
        session.commit()
        try:
            existing = session.scalar(select(Transcript).where(Transcript.source_hash == job.source_hash))
            if existing:
                job.transcript_id = existing.id
            elif job.source_type == "pdf": result = extract_pdf(job.source_ref)
            elif job.source_type in {"audio", "video"}: result = transcribe_media(job.source_ref, job.source_type, settings.whisper_model)
            else: result = resolve_link(job.source_ref, settings.storage_dir / "ingest", settings.whisper_model, settings.max_duration_seconds)
            if not existing:
                transcript = Transcript(source_hash=job.source_hash or sha256(job.source_ref.encode()).hexdigest(), source_type=result.source_type, source_meta=result.source_meta, raw_text=result.raw_text, segments=[item.model_dump() for item in result.segments])
                session.add(transcript); session.flush(); job.transcript_id = transcript.id
            _transition(job, "queued", "generation")
            session.commit()
        except Exception as exc:
            _transition(job, "failed", "ingestion", str(exc)); session.commit(); raise


def generate_job(job_id: str, category: str | None = None, provider_name: str | None = None) -> None:
    """Generate canonical notes from an already-persisted transcript only."""
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        if not job or not job.transcript_id: raise ValueError("Transcript not found")
        transcript = session.get(Transcript, job.transcript_id)
        _transition(job, "generating_notes", "generation"); session.commit()
        try:
            selected = category or job.category
            notes = generate_notes(get_provider(provider_name or job.provider), selected, str(transcript.source_meta.get("title", "Untitled")), transcript.raw_text)
            item = NotesResult(transcript_id=transcript.id, category=selected, canonical_json=notes.model_dump(mode="json"))
            session.add(item); session.flush()
            job.notes_result_id, job.category = item.id, selected
            _transition(job, "queued", "formatting"); session.commit()
        except Exception as exc:
            _transition(job, "failed", "generation", str(exc)); session.commit(); raise


def format_job(job_id: str, formats: list[str] | None = None) -> None:
    """Render selected formats from existing canonical notes without an LLM call."""
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        if not job or not job.notes_result_id: raise ValueError("Notes result not found")
        notes = session.get(NotesResult, job.notes_result_id)
        _transition(job, "formatting", "formatting"); session.commit()
        try:
            from core.categories.registry import get_category_model
            model = get_category_model(notes.category).model_validate(notes.canonical_json)
            destination = settings.storage_dir / "artifacts" / job.id
            destination.mkdir(parents=True, exist_ok=True)
            for name in formats or job.formats:
                data, content_type, extension = render_format(name, model)
                path = destination / f"notes.{extension}"
                path.write_bytes(data)
                session.add(Artifact(job_id=job.id, notes_result_id=notes.id, format=name, path=str(path), content_type=content_type))
            _transition(job, "done", "done"); session.commit()
        except Exception as exc:
            _transition(job, "failed", "formatting", str(exc)); session.commit(); raise


@celery_app.task(name="cortex.run_pipeline")
def run_pipeline(job_id: str) -> None:
    """Execute the complete staged pipeline in a Celery worker."""
    ingest_job(job_id); generate_job(job_id); format_job(job_id)


@celery_app.task(name="cortex.run_generation")
def run_generation(job_id: str, category: str, provider_name: str | None = None) -> None:
    """Execute generation and formatting while deliberately skipping ingestion."""
    generate_job(job_id, category, provider_name); format_job(job_id)


@celery_app.task(name="cortex.run_format")
def run_format(job_id: str, formats: list[str]) -> None:
    """Execute only format rendering for an existing notes result."""
    format_job(job_id, formats)
