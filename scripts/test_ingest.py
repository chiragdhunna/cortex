"""Run one ingestion adapter and print its normalized JSON output."""
import argparse
from pathlib import Path
from ingestion.link_resolver import resolve_link
from ingestion.pdf_extractor import extract_pdf
from ingestion.transcriber import transcribe_media


def main() -> None:
    """Parse command-line input and execute the selected adapter."""
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["pdf", "audio", "video", "link"])
    parser.add_argument("source")
    parser.add_argument("--whisper-model", default="base")
    args = parser.parse_args()
    if args.kind == "pdf":
        result = extract_pdf(args.source)
    elif args.kind == "link":
        result = resolve_link(args.source, Path("storage/ingest"), args.whisper_model)
    else:
        result = transcribe_media(args.source, args.kind, args.whisper_model)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
