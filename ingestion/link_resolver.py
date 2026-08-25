"""Link ingestion through yt-dlp, preferring available captions."""
from pathlib import Path
from urllib.parse import urlparse
import yt_dlp
from ingestion.schemas import IngestionResult, Segment
from ingestion.transcriber import transcribe_media


def _is_youtube(url: str) -> bool:
    """Return whether a URL belongs to a recognized YouTube host."""
    return urlparse(url).hostname in {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"}


def _vtt_to_result(path: Path, source_type: str, title: str) -> IngestionResult:
    """Convert a downloaded WebVTT caption file into normalized text."""
    segments: list[Segment] = []
    start = 0.0
    for line in path.read_text(errors="replace").splitlines():
        if " --> " in line:
            stamp = line.split(" --> ")[0].replace(",", ".")
            pieces = stamp.split(":")
            start = float(pieces[-1]) + 60 * float(pieces[-2]) + (3600 * float(pieces[-3]) if len(pieces) == 3 else 0)
        elif line.strip() and not line.startswith(("WEBVTT", "Kind:", "Language:")) and "-->" not in line and not line.strip().isdigit():
            text = line.strip()
            if not segments or segments[-1].text != text:
                segments.append(Segment(start=start, end=start, text=text))
    raw_text = " ".join(item.text for item in segments)
    if not raw_text:
        raise ValueError("Caption file contained no text")
    return IngestionResult(source_type=source_type, source_meta={"title": title, "captions_used": True}, raw_text=raw_text, segments=segments)


def resolve_link(url: str, work_dir: str | Path, model_size: str = "base", max_duration_seconds: int | None = None) -> IngestionResult:
    """Download captions or audio for a supported media URL, then normalize it."""
    destination = Path(work_dir)
    destination.mkdir(parents=True, exist_ok=True)
    source_type = "video_link" if _is_youtube(url) else "audio_link"
    options: dict[str, object] = {"quiet": True, "noplaylist": True, "outtmpl": str(destination / "%(id)s.%(ext)s")}
    with yt_dlp.YoutubeDL({**options, "skip_download": True}) as downloader:
        info = downloader.extract_info(url, download=False)
    if max_duration_seconds and info.get("duration") and float(info["duration"]) > max_duration_seconds:
        raise ValueError(f"Media duration exceeds configured limit of {max_duration_seconds} seconds")
    title = str(info.get("title", url))
    if source_type == "video_link" and (info.get("subtitles") or info.get("automatic_captions")):
        caption_options = {**options, "skip_download": True, "writesubtitles": True, "writeautomaticsub": True, "subtitlesformat": "vtt", "subtitleslangs": ["en", "en.*"]}
        with yt_dlp.YoutubeDL(caption_options) as downloader:
            downloader.download([url])
        captions = list(destination.glob("*.vtt"))
        if captions:
            return _vtt_to_result(captions[0], source_type, title)
    media_options = {**options, "format": "bestaudio/best", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]}
    with yt_dlp.YoutubeDL(media_options) as downloader:
        downloader.download([url])
    files = [item for item in destination.iterdir() if item.suffix.lower() in {".mp3", ".m4a", ".wav", ".webm", ".mp4"}]
    if not files:
        raise ValueError("Unable to download media from link")
    result = transcribe_media(files[0], source_type, model_size)
    result.source_meta["title"] = title
    return result
