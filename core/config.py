"""Application configuration loaded from environment variables."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration with safe local-first defaults."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    gemini_api_key: str | None = None
    database_url: str = "sqlite:///./cortex.db"
    redis_url: str = "redis://localhost:6379/0"
    whisper_model: str = "base"
    max_upload_mb: int = 500
    max_duration_seconds: int = 10800
    retention_days: int = 30
    storage_dir: Path = Path("storage")


settings = Settings()
