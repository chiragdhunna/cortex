"""Local faster-whisper transcription adapter."""
from pathlib import Path
from ingestion.schemas import IngestionResult, Segment


def transcribe_media(path: str | Path, source_type: str, model_size: str = "base") -> IngestionResult:
    """Transcribe audio or video locally and return timed normalized text.

    The import is deliberately lazy so PDF-only usage does not require loading the
    Whisper runtime until it is actually needed.
    """
    if source_type not in {"audio", "video", "audio_link", "video_link"}:
        raise ValueError(f"Unsupported transcribable source type: {source_type}")
    from faster_whisper import WhisperModel
    source = Path(path)
    model = WhisperModel(model_size)
    whisper_segments, info = model.transcribe(str(source), vad_filter=True)
    segments = [Segment(start=item.start, end=item.end, text=item.text.strip()) for item in whisper_segments]
    raw_text = " ".join(segment.text for segment in segments if segment.text)
    if not raw_text:
        raise ValueError("Transcription produced no text")
    return IngestionResult(
        source_type=source_type,  # type: ignore[arg-type]
        source_meta={"title": source.stem, "duration_sec": getattr(info, "duration", 0)},
        raw_text=raw_text,
        segments=segments,
    )
