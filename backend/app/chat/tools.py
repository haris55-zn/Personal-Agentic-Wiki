"""Tool read-only untuk agent: `note_search`, `note_read`, `web_search`.

BELAJAR — apa itu "tool" di pydantic-ai:
  Tool = fungsi Python biasa yang DIDAFTARKAN ke agent, sehingga LLM bisa
  MEMANGGILNYA. Pydantic-ai membangun JSON Schema argumen OTOMATIS dari
  type hint + docstring, lalu mengirim schema itu ke LLM.

  - docstring = PETUNJUK yang dibaca LLM (kapan dipakai, format argumen).
  - type hint = skema argumen (LLM wajib mengisi).
  - nilai return = hasil yang DIBACA LLM (observation) → muncul di `react observation`.

  Dua cara tool butuh "state aplikasi":
  - `note_search` / `web_search`: mandiri (chunk store / network), tanpa `ctx`.
  - `note_read`: butuh SESI DB → injeksi lewat `RunContext[Session]` (lihat
    `deps_type` di agent.py + `agent.run(..., deps=session)`).
"""
import asyncio
import logging

from ddgs import DDGS
from pydantic_ai import RunContext
from sqlmodel import Session

from app.notes.crud import get_note
from app.search.service import search_wiki

_log = logging.getLogger(__name__)


def note_search(query: str) -> str:
    """Cari note di wiki lokal. `query`: kata kunci (boleh beberapa kata).
    Balas daftar "slug — judul (snippet)" yang cocok, atau "tidak ada note yang cocok"."""
    hits = search_wiki(query, 3)
    if not hits:
        return "tidak ada note yang cocok"
    lines = [f"{h.slug} — {h.title}\n   {h.snippet}" for h in hits]
    return f"{len(hits)} note cocok:\n" + "\n".join(lines)


def note_read(ctx: RunContext[Session], slug: str) -> str:
    """Baca isi PENUH satu note (`slug` dari hasil note_search).
    Balas judul + isi markdown, atau "note '<slug>' tidak ditemukan"."""
    note = get_note(ctx.deps, slug)
    if note is None:
        return f"note '{slug}' tidak ditemukan"
    return f"# {note.title}\n\n{note.content}"


# Klien DuckDuckGo dibuat sekali (singleton). `.text()` = panggilan jaringan blocking.
# backend="lite": endpoint html.duckduckgo.com kerap di-blok/rate-limit (case
# timeout yang membunuh sesi). lite (lite.duckduckgo.com) tembus. Cadangan: "bing".
_ddg_client = DDGS()


def _format_web(results: list[dict]) -> str:
    """Susun hasil web menjadi string ringkas untuk LLM (observation)."""
    if not results:
        return "tidak ada hasil web"
    return "\n".join(f"{r['title']} — {r['href']}\n   {r['body']}" for r in results)


async def web_search(query: str) -> str:
    """Cari di internet via DuckDuckGo. `query`: kata kunci.
    Balas daftar "judul — URL (ringkasan)", atau "tidak ada hasil web"."""
    # `.text()` BLOKIR (network). Tool async tak boleh memanggilnya langsung di
    # event loop — pindahkan ke thread via `asyncio.to_thread` agar loop tak macet.
    try:
        results = await asyncio.to_thread(_ddg_client.text, query, max_results=5, backend="lite")
    except Exception as exc:  # noqa: BLE001 — DDG timeout/diblokir (network)
        # Satu tool gagal TAK BOLEH mematikan seluruh sesi agen. Balas status
        # terdegradasi supaya LLM tetap bisa menjawab wajar (bilang web tak tersedia).
        _log.warning("web search gagal: %s", exc)
        return (
            f"web search GAGAL ({type(exc).__name__}). "
            "Sampaikan ke user bahwa pencarian web sedang tidak tersedia."
        )
    return _format_web(results)