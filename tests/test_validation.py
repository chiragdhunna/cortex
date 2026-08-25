import pytest
from core.validation import validate_media_duration


def test_duration_validation_accepts_unknown_and_rejects_over_limit(monkeypatch):
    """Unknown duration does not reject a source, while a known long one does."""
    import core.validation as validation
    monkeypatch.setattr(validation, "media_duration_seconds", lambda _: 0)
    validate_media_duration("unknown", 10)
    monkeypatch.setattr(validation, "media_duration_seconds", lambda _: 11)
    with pytest.raises(ValueError, match="duration"):
        validate_media_duration("long", 10)
