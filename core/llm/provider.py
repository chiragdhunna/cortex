"""Minimal provider abstraction for all LLM backends."""
from typing import Protocol
from pydantic import BaseModel


class LLMProvider(Protocol):
    """A provider capable of returning a raw JSON response to a prompt."""
    def generate_raw(self, prompt: str) -> str:
        """Generate a response that is expected to contain JSON only."""

    def generate_json(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        """Generate and validate a response against the requested schema."""
