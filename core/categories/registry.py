"""Category registry, isolated from ingestion and formatting."""
from pydantic import BaseModel
from core.categories.schemas import CATEGORY_MODELS


def get_category_model(category: str) -> type[BaseModel]:
    """Return the canonical envelope model registered for a category."""
    try:
        return CATEGORY_MODELS[category]
    except KeyError as exc:
        raise ValueError(f"Unsupported category: {category}") from exc
