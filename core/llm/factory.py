"""Provider factory controlled by a global or per-job provider name."""
from core.config import settings
from core.llm.gemini import GeminiProvider
from core.llm.ollama import OllamaProvider
from core.llm.provider import LLMProvider


def get_provider(name: str | None = None) -> LLMProvider:
    """Construct the configured Gemini or Ollama provider."""
    selected = name or settings.llm_provider
    if selected == "ollama": return OllamaProvider()
    if selected == "gemini": return GeminiProvider()
    raise ValueError(f"Unsupported LLM provider: {selected}")
