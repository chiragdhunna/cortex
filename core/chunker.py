"""Semantic-ish text chunking for bounded LLM context windows."""
import re
from pydantic import BaseModel


class TextChunk(BaseModel):
    """A coherent piece of source text with its ordinal position."""
    index: int
    text: str


def chunk_text(text: str, target_tokens: int = 2000, overlap_tokens: int = 120) -> list[TextChunk]:
    """Split text near paragraph or sentence boundaries with a small word overlap.

    Token counts are estimated as four characters per token, which is sufficient for
    provider-agnostic context budgeting without importing a model-specific tokenizer.
    """
    if target_tokens <= 0 or overlap_tokens < 0:
        raise ValueError("target_tokens must be positive and overlap_tokens non-negative")
    limit = target_tokens * 4
    overlap = overlap_tokens * 4
    units = [unit.strip() for unit in re.split(r"\n\s*\n", text) if unit.strip()]
    if not units:
        return []
    chunks: list[str] = []
    current = ""
    for unit in units:
        sentences = re.split(r"(?<=[.!?])\s+", unit)
        for sentence in sentences:
            if not sentence:
                continue
            proposed = f"{current} {sentence}".strip()
            if current and len(proposed) > limit:
                chunks.append(current)
                suffix = current[-overlap:].split(" ", 1)
                carry = suffix[-1] if len(current) > overlap and len(suffix) > 1 else current[-overlap:]
                current = f"{carry} {sentence}".strip()
            else:
                current = proposed
    if current:
        chunks.append(current)
    return [TextChunk(index=index, text=value) for index, value in enumerate(chunks)]
