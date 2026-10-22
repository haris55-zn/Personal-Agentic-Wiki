"""Konfigurasi aplikasi — tervalidasi Pydantic, dibaca dari `.env`."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Folder `backend/` (tiga tingkat di atas file ini) dan folder data runtime-nya.
BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    """Satu tempat semua nilai konfigurasi — otomatis dibaca & divalidasi."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = "deepseek-v4-pro"
    embedding_model: str = "BAAI/bge-m3"
    db_path: Path = DATA_DIR / "paw.db"
    chroma_path: Path = DATA_DIR / "chroma"


settings = Settings()