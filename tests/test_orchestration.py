from core.database import Base, engine, init_database, SessionLocal
from core.models import Job, NotesResult, Transcript
from jobs import tasks


def test_regenerate_and_format_do_not_call_earlier_stages(monkeypatch):
    Base.metadata.drop_all(engine); init_database()
    with SessionLocal() as db:
        transcript = Transcript(source_hash="x", source_type="pdf", source_meta={"title":"t"}, raw_text="text", segments=[])
        db.add(transcript); db.flush()
        notes = NotesResult(transcript_id=transcript.id, category="exam", canonical_json={"category":"exam", "source_title":"t", "generated_at":"2025-01-01T00:00:00Z", "topics":[{"title":"a","content":{"definitions":[],"summary":"s","self_test":[]}}]})
        db.add(notes); db.flush(); job = Job(source_type="pdf", source_ref="x", source_hash="x", category="exam", formats=["json"], transcript_id=transcript.id, notes_result_id=notes.id); db.add(job); db.commit()
        job_id = job.id
    monkeypatch.setattr(tasks, "ingest_job", lambda _: (_ for _ in ()).throw(AssertionError("ingestion called")))
    monkeypatch.setattr(tasks, "generate_job", lambda *_args: None)
    tasks.run_generation.run(job_id, "exam")
    monkeypatch.setattr(tasks, "generate_job", lambda *_args: (_ for _ in ()).throw(AssertionError("generation called")))
    tasks.run_format.run(job_id, ["json"])
