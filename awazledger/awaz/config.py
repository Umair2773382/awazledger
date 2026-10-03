"""Configuration — everything comes from environment variables (.env)."""
import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_base_url: str = field(
        default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    )
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "openai/gpt-oss-20b"))
    whisper_model: str = field(default_factory=lambda: os.getenv("WHISPER_MODEL", "small"))
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "data/ledger.db"))


settings = Settings()
