"""Gemini hosted provider, activated only when a key is configured."""
from pydantic import BaseModel
from core.config import settings


class GeminiProvider:
    """Generate JSON using Gemini's structured response configuration."""
    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key or settings.gemini_api_key
        self.model = model
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiProvider")

    def generate_raw(self, prompt: str) -> str:
        """Generate JSON text from Gemini."""
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return response.text

    def generate_json(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        """Generate and validate Gemini output."""
        return schema.model_validate_json(self.generate_raw(prompt))
