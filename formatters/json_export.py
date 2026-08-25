"""Pretty JSON canonical-notes formatter."""
from pydantic import BaseModel
from formatters.registry import register_format


@register_format("json")
def render_json(notes: BaseModel) -> tuple[bytes, str, str]:
    """Serialize canonical notes exactly for inline viewing or download."""
    return notes.model_dump_json(indent=2).encode(), "application/json", "json"
