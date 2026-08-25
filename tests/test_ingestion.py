import fitz
from ingestion.pdf_extractor import extract_pdf
from ingestion.transcriber import transcribe_media


def test_pdf_extraction_normalizes_pages(tmp_path):
    pdf = tmp_path / "lesson.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Lesson heading\nUseful detail.")
    document.save(pdf)
    document.close()
    result = extract_pdf(pdf)
    assert result.source_type == "pdf"
    assert result.source_meta["page_count"] == 1
    assert "Lesson heading" in result.raw_text


def test_transcriber_normalizes_whisper_segments(monkeypatch, tmp_path):
    """Exercise the adapter contract without downloading a Whisper model in CI."""
    class FakeSegment:
        start, end, text = 0.0, 1.5, " short audio sample "

    class FakeInfo:
        duration = 1.5

    class FakeModel:
        def __init__(self, _size): pass
        def transcribe(self, _path, vad_filter): return iter([FakeSegment()]), FakeInfo()

    import sys, types
    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=FakeModel))
    result = transcribe_media(tmp_path / "sample.wav", "audio")
    assert result.raw_text == "short audio sample"
    assert result.segments[0].end == 1.5
