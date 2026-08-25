"""Typed contract emitted by every ingestion adapter."""
from typing import Literal
from pydantic import BaseModel, Field

SourceType = Literal["pdf", "audio", "video", "video_link", "audio_link"]


class Segment(BaseModel):
    """A timed fragment of normalized source text."""
    start: float
    end: float
    text: str


class IngestionResult(BaseModel):
    """Canonical output of the ingestion layer."""
    source_type: SourceType
    source_meta: dict[str, object] = Field(default_factory=dict)
    raw_text: str
    segments: list[Segment] = Field(default_factory=list)
