"""Schema-inline prompts for each registered category."""
import json
from pydantic import BaseModel
from core.categories.registry import get_category_model


def build_notes_prompt(category: str, source_title: str, text: str, synthesis: bool = False) -> str:
    """Build a strict JSON-only prompt for a chunk or final synthesis pass."""
    model: type[BaseModel] = get_category_model(category)
    operation = "Synthesize, de-duplicate, and order these extracted notes" if synthesis else "Extract useful notes"
    return f"""{operation} for category '{category}' from source '{source_title}'.
Return ONLY a JSON object that validates against this JSON Schema:
{json.dumps(model.model_json_schema(), indent=2)}
Never add markdown, commentary, or fields outside the schema.
Source material:
---
{text}
---"""
