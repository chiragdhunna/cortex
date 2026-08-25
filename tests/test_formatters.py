from core.categories.schemas import ExamNotes
from formatters.registry import registered_formats, render_format
import formatters  # noqa: F401


def sample():
    return ExamNotes.model_validate({"category":"exam", "source_title":"Test", "generated_at":"2025-01-01T00:00:00Z", "topics":[{"title":"One", "content":{"definitions":[{"term":"A", "definition":"B"}], "summary":"S", "self_test":[{"q":"Q", "a":"A"}]}}]})


def test_every_formatter_renders_from_canonical_fixture():
    assert registered_formats() == {"markdown", "json", "anki_csv", "pdf"}
    for name in registered_formats():
        data, content_type, extension = render_format(name, sample())
        assert data and content_type and extension
