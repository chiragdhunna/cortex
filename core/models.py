"""SQLAlchemy persistence models for jobs and pipeline products."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


def utcnow() -> datetime:
    """Return a naive UTC timestamp compatible with SQLite."""
    return datetime.utcnow()


class Job(Base):
    """A submitted pipeline request and its current state."""
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_type: Mapped[str] = mapped_column(String(32))
    source_ref: Mapped[str] = mapped_column(Text)
    source_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(32))
    formats: Mapped[list[str]] = mapped_column(JSON, default=list)
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    stage: Mapped[str] = mapped_column(String(32), default="queued")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    transcript_id: Mapped[str | None] = mapped_column(ForeignKey("transcripts.id"), nullable=True)
    notes_result_id: Mapped[str | None] = mapped_column(ForeignKey("notes_results.id"), nullable=True)
    transcript: Mapped["Transcript | None"] = relationship(foreign_keys=[transcript_id])
    notes_result: Mapped["NotesResult | None"] = relationship(foreign_keys=[notes_result_id])


class Transcript(Base):
    """Normalized source text retained independently of a notes generation."""
    __tablename__ = "transcripts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_hash: Mapped[str] = mapped_column(String(64), index=True)
    source_type: Mapped[str] = mapped_column(String(32))
    source_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_text: Mapped[str] = mapped_column(Text)
    segments: Mapped[list[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class NotesResult(Base):
    """Validated canonical notes JSON generated from a transcript."""
    __tablename__ = "notes_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    transcript_id: Mapped[str] = mapped_column(ForeignKey("transcripts.id"))
    category: Mapped[str] = mapped_column(String(32))
    canonical_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Artifact(Base):
    """One rendered downloadable output for a notes result."""
    __tablename__ = "artifacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    notes_result_id: Mapped[str] = mapped_column(ForeignKey("notes_results.id"))
    format: Mapped[str] = mapped_column(String(32))
    path: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
