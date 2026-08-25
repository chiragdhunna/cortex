import json
import pytest
from core.notes_generator import GenerationSchemaInvalid, generate_notes


class FakeOllama:
    def __init__(self, responses): self.responses = iter(responses)
    def generate_raw(self, _prompt): return next(self.responses)
    def generate_json(self, prompt, schema): return schema.model_validate_json(self.generate_raw(prompt))


def exam_json():
    return json.dumps({"category":"exam", "source_title":"source", "generated_at":"2025-01-01T00:00:00Z", "topics":[{"title":"topic", "content":{"definitions":[], "summary":"summary", "self_test":[]}}]})


def test_ollama_style_invalid_json_retries_then_validates():
    result = generate_notes(FakeOllama(["not json", exam_json()]), "exam", "source", "A short source.")
    assert result.category == "exam"


def test_generation_fails_with_specific_error_after_two_retries():
    with pytest.raises(GenerationSchemaInvalid, match="generation_schema_invalid"):
        generate_notes(FakeOllama(["bad", "bad", "bad"]), "exam", "source", "A short source.")
