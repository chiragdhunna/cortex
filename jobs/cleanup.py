"""Retention cleanup for generated local storage artifacts."""
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import select
from core.config import settings
from core.database import SessionLocal
from core.models import Artifact
from jobs.celery_app import celery_app


@celery_app.task(name="cortex.cleanup_expired_artifacts")
def cleanup_expired_artifacts(retention_days: int | None = None) -> int:
    """Delete expired artifact files and their database rows, returning count."""
    cutoff = datetime.utcnow() - timedelta(days=retention_days or settings.retention_days)
    with SessionLocal() as session:
        items = session.scalars(select(Artifact).where(Artifact.created_at < cutoff)).all()
        for item in items:
            Path(item.path).unlink(missing_ok=True)
            session.delete(item)
        session.commit()
        return len(items)
