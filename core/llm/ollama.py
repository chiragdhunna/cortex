"""Local no-key Ollama provider."""
import json
import httpx
from pydantic import BaseModel
from core.config import settings


class OllamaProvider:
    """Use Ollama's local REST endpoint with JSON response mode."""
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model

    def generate_raw(self, prompt: str) -> str:
        """Call local Ollama; no credential is sent or required."""
        response = httpx.post(f"{self.base_url}/api/generate", json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"}, timeout=300)
        response.raise_for_status()
        return str(response.json()["response"])

    def generate_json(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        """Generate raw JSON then validate it with Pydantic."""
        return schema.model_validate_json(self.generate_raw(prompt))
