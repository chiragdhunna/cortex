"""Format registry whose renderers only consume canonical notes objects."""
from collections.abc import Callable
from pydantic import BaseModel

Formatter = Callable[[BaseModel], tuple[bytes, str, str]]
_FORMATTERS: dict[str, Formatter] = {}


def register_format(name: str) -> Callable[[Formatter], Formatter]:
    """Register a formatter without coupling it to categories or generation."""
    def decorator(function: Formatter) -> Formatter:
        _FORMATTERS[name] = function
        return function
    return decorator


def render_format(name: str, notes: BaseModel) -> tuple[bytes, str, str]:
    """Render canonical notes into bytes, media type, and file extension."""
    try:
        return _FORMATTERS[name](notes)
    except KeyError as exc:
        raise ValueError(f"Unsupported format: {name}") from exc


def registered_formats() -> set[str]:
    """Return available output names."""
    return set(_FORMATTERS)
