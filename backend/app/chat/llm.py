"""Model LLM (OpenAI-compatible) untuk agent chat — MATERI pydantic-ai.

BELAJAR — 3 konsep inti pydantic-ai di file ini:

1. MODEL — kelas yang tahu CARA memanggil satu API LLM.
   `OpenAIChatModel` = kelas yang memanggil Chat Completions lewat SDK
   `openai`. Nama model (mis. "qwen3.8-max", "deepseek-v4-pro") bukan
   bagian dari kelasnya — dia ARGUMEN `model_name`.

2. PROVIDER — kelas yang memegang ENDPOINT + AUTENTIKASI layanan.
   `OpenAIProvider(base_url=..., api_key=...)`. Karena provider kita adalah
   endpoint OpenAI-COMPATIBLE (QwenCloud / OpenCode / Gemini), kita set
   `base_url` kustom — bukan preset `openai:` yang menunjuk api.openai.com.

3. TITIK TEMU — `OpenAIChatModel(nama_model, provider=OpenAIProvider(...))`
   menghasilkan SATU objek `model`. Objek ini nanti diserahkan ke `Agent`.

Alur (dibaca bawah-ke-atas):
   Agent ──pakai──▶ OpenAIChatModel ──pakai──▶ OpenAIProvider ──HTTP──▶ LLM

Kenapa di-cache (`lru_cache`): membangun objek model itu MURAH dan TIDAK
ada network — tapi kita cuma butuh SATU instance untuk seluruh proses
(singleton), supaya tiap request tidak membangun ulang.
"""
from functools import lru_cache

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.core.config import settings


@lru_cache(maxsize=1)
def build_model() -> OpenAIChatModel:
    """Bangun Model+Provider sekali. Nilai dibaca dari `.env` (lewat `settings`).

    `or None`: bila `.env` belum diisi (default kosong), kita biarkan provider
    memakai fallback-nya (env `OPENAI_API_KEY` & url default). Normalnya user
    mengisi lewat `uv run python -m app.cli set-llm`.
    """
    return OpenAIChatModel(
        settings.llm_model,
        provider=OpenAIProvider(
            base_url=settings.llm_base_url or None,
            api_key=settings.llm_api_key or None,
        ),
    )