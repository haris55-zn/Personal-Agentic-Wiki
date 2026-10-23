"""Agent ReAct (LLM + tool) + terjemahan hasil → event SSE frontend.

BELAJAR — apa itu `Agent`:
  `Agent` = LLM + system prompt + daftar tool, disatukan jadi SATU "pekerja".
  Saat `run(prompt)` dipanggil, pydantic-ai menjalankan loop ReAct OTOMATIS:
    1. kirim prompt ke LLM;
    2. LLM putuskan: jawab langsung ATAU panggil tool;
    3. kalau tool dipanggil, pydantic-ai EKSEKUSI tool lalu umpan hasilnya balik
       ke LLM (ulangi ke 2) — berulang sampai LLM menjawab final.
  Kita TIDAK menulis loop while/repeat sendiri — pydantic-ai yang memegangnya.

BELAJAR — `deps` (dependency injection):
  `note_read` butuh sesi DB. Caranya: `deps_type=Session` di `Agent`, lalu tool
  yang butuh state mendeklarasikan `ctx: RunContext[Session]` sebagai param
  pertama. Saat `run(..., deps=session)` dipanggil, pydantic-ai menyuntik sesi
  itu ke `ctx.deps` — tanpa variabel global, tanpa thread-local.

BELAJAR — `all_messages()` = jantung pemetaan ini:
  Setelah `run()`, `result.all_messages()` berisi transkrip LENGKAP urut waktu:
     request(user) → response(tool-call) → request(tool-return) → response(text)
  Kita pindai part `tool-call` (→ action) & `tool-return` (→ observation), lalu
  jawaban akhir = `result.output` (→ answer).
"""
import json

from pydantic_ai import Agent
from sqlmodel import Session

from app.chat.llm import build_model
from app.chat.tools import note_read, note_search, web_search
from app.edits.extract import extract_drafts
from app.edits.tools import note_write

SYSTEM_PROMPT = """\
Kamu asisten wiki pribadi "paw" (sekumpulan note markdown lokal).

Alat (tool) yang tersedia:
- note_search: cari note berdasarkan kata kunci.
- note_read: baca isi penuh satu note (slug dari hasil note_search).
- web_search: cari di internet (DuckDuckGo) bila info tidak ada di wiki.
- note_write: usulkan buat/ubah note (HANYA draft — user yang Apply).

Aturan urutan (routing):
1. Pertanyaan isi wiki → WAJIB note_search dulu; butuh detail/kutip → note_read(slug).
2. Fakta umum/terkini yang TIDAK ada di wiki → web_search.
3. Jangan panggil dua tool sekaligus; selesaikan satu dulu.
4. Jawab singkat & langsung ke inti, dalam bahasa user (umumnya Indonesia).
5. Jangan mengarang isi. Bila tak ketemu di mana pun, katakan tak ketemu + sarankan kata kunci lain.
6. Bila user minta buat/ubah note, usulkan lewat note_write (draft, belum menulis). slug = huruf kecil, dipisah "-".
"""


def build_agent() -> Agent:
    """Bangun agent (LLM + 4 tool + deps sesi DB) — dipakai seluruh proses."""
    return Agent(
        build_model(),
        deps_type=Session,
        system_prompt=SYSTEM_PROMPT,
        tools=[note_search, note_read, web_search, note_write],
    )


def _map_message(message) -> list[dict]:
    """Pindai SATU `ModelMessage` → daftar event `react` (action/observation).

    `part.part_kind` mendiskriminasi jenis part:
      - "tool-call"   → LLM minta panggil tool (action).
      - "tool-return" → hasil eksekusi tool (observation).
      - "text"/"user-prompt"/"system-prompt" → diabaikan (bukan react).
    """
    events: list[dict] = []
    for part in message.parts:
        kind = getattr(part, "part_kind", None)
        if kind == "tool-call":
            args = part.args
            # note_write membawa content markdown (bisa panjang); jejak cukup butuh intinya.
            if part.tool_name == "note_write":
                args = {k: part.args.get(k) for k in ("action", "slug", "title")}
            events.append({
                "event": "react",
                "step": "action",
                "tool": part.tool_name,
                "args": json.dumps(args, ensure_ascii=False),
            })
        elif kind == "tool-return":
            events.append({
                "event": "react",
                "step": "observation",
                "content": str(part.content),
            })
    return events


async def stream_events(message: str, session: Session):
    """Jalankan agent untuk `message` + sesi DB (deps), hasilkan event SSE frontend.

    Urutan: (react action → react observation)* → answer.
    `result.output` = teks jawaban final (default `output_type=str`).
    """
    agent = build_agent()
    result = await agent.run(message, deps=session)
    for msg in result.all_messages():
        for ev in _map_message(msg):
            yield ev
    yield {"event": "answer", "content": result.output}
    for draft in extract_drafts(result.all_messages(), session):
        yield {"event": "draft", **draft}