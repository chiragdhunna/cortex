"""Pydantic canonical notes schemas, one distinct shape per category."""
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field


class QAPair(BaseModel):
    """An interview question, concise answer, and estimated difficulty."""
    q: str
    a: str
    difficulty: Literal["easy", "medium", "hard"]


class InterviewContent(BaseModel):
    """Recall-oriented notes for an interview candidate."""
    qa_pairs: list[QAPair] = Field(default_factory=list)
    talking_points: list[str] = Field(default_factory=list)
    gotchas: list[str] = Field(default_factory=list)


class Definition(BaseModel):
    """A term and its study definition."""
    term: str
    definition: str


class SelfTest(BaseModel):
    """A question and answer for self-assessment."""
    q: str
    a: str


class ExamContent(BaseModel):
    """Exam preparation notes."""
    definitions: list[Definition] = Field(default_factory=list)
    summary: str
    self_test: list[SelfTest] = Field(default_factory=list)


class ConceptMap(BaseModel):
    """A graph simple enough for a frontend to render directly."""
    nodes: list[str] = Field(default_factory=list)
    edges: list[tuple[str, str]] = Field(default_factory=list)


class UnderstandingContent(BaseModel):
    """Deep-learning-oriented explanation notes."""
    explanation: str
    analogies: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    concept_map: ConceptMap


class InterviewTopic(BaseModel):
    """A named interview topic."""
    title: str
    content: InterviewContent


class ExamTopic(BaseModel):
    """A named exam topic."""
    title: str
    content: ExamContent


class UnderstandingTopic(BaseModel):
    """A named understanding topic."""
    title: str
    content: UnderstandingContent


class InterviewNotes(BaseModel):
    """Canonical envelope for interview notes."""
    category: Literal["interview"]
    source_title: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    topics: list[InterviewTopic]


class ExamNotes(BaseModel):
    """Canonical envelope for exam notes."""
    category: Literal["exam"]
    source_title: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    topics: list[ExamTopic]


class UnderstandingNotes(BaseModel):
    """Canonical envelope for understanding notes."""
    category: Literal["understanding"]
    source_title: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    topics: list[UnderstandingTopic]


CanonicalNotes = InterviewNotes | ExamNotes | UnderstandingNotes
CATEGORY_MODELS = {"interview": InterviewNotes, "exam": ExamNotes, "understanding": UnderstandingNotes}
