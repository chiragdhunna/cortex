"""Category-aware, format-agnostic canonical notes generation."""
from pydantic import BaseModel, ValidationError
from core.category_prompts import build_notes_prompt
from core.categories.registry import get_category_model
from core.chunker import chunk_text
from core.llm.provider import LLMProvider


class GenerationSchemaInvalid(RuntimeError):
    """Raised after the provider exhausts corrective JSON retries."""


def _validated(provider: LLMProvider, prompt: str, model: type[BaseModel]) -> BaseModel:
    """Ask a provider and retry at most twice with validation feedback."""
    current_prompt = prompt
    for attempt in range(3):
        raw = provider.generate_raw(current_prompt)
        try:
            return model.model_validate_json(raw)
        except ValidationError as exc:
            if attempt == 2:
                raise GenerationSchemaInvalid("generation_schema_invalid") from exc
            current_prompt = f"Your prior response was invalid: {exc.errors()}. Return only valid JSON matching this schema: {model.model_json_schema()}"
    raise AssertionError("unreachable")


def generate_notes(provider: LLMProvider, category: str, source_title: str, raw_text: str) -> BaseModel:
    """Map source chunks then synthesize them into one validated canonical envelope."""
    model = get_category_model(category)
    chunks = chunk_text(raw_text) or []
    if not chunks:
        raise ValueError("Cannot generate notes from empty text")
    extracted = [_validated(provider, build_notes_prompt(category, source_title, chunk.text), model) for chunk in chunks]
    if len(extracted) == 1:
        return extracted[0]
    payload = "\n\n".join(item.model_dump_json() for item in extracted)
    return _validated(provider, build_notes_prompt(category, source_title, payload, synthesis=True), model)
