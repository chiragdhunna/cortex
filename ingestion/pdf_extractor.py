"""PDF-to-text ingestion using PyMuPDF."""
from pathlib import Path
import fitz
from ingestion.schemas import IngestionResult, Segment


def extract_pdf(path: str | Path) -> IngestionResult:
    """Extract page text from a PDF into the normalized ingestion contract.

    Page headings are retained naturally by PyMuPDF's layout-oriented text extraction.
    """
    source = Path(path)
    document = fitz.open(source)
    pages: list[str] = []
    segments: list[Segment] = []
    try:
        for index, page in enumerate(document):
            text = page.get_text("text").strip()
            if text:
                pages.append(text)
                segments.append(Segment(start=float(index), end=float(index + 1), text=text))
    finally:
        document.close()
    raw_text = "\n\n".join(pages)
    if not raw_text:
        raise ValueError("PDF contains no extractable text")
    return IngestionResult(
        source_type="pdf",
        source_meta={"title": source.stem, "page_count": len(segments)},
        raw_text=raw_text,
        segments=segments,
    )
