"""Agent editor (propose): usulkan revisi note → answer (teks) + draft (terstruktur).

Alurnya: endpoint pre-fetch note (router), lalu agent diberi isi note + instruksi.
Agent boleh memanggil `note_write` (draft) lalu memberi jawaban teks (`result.output`).
"""
from pydantic_ai import Agent

from app.chat.llm import build_model
from app.edits import extract
from app.edits.tools import note_write
from app.notes.models import Note
from sqlmodel import Session

EDIT_PROMPT = """\
Kamu editor note di wiki "paw". Diberi isi note + instruksi revisi dari user.

Tugas:
1. Usulkan perubahan lewat tool note_write (ini HANYA draft, belum ditulis).
2. Lalu jawab SATU kalimat: apa yang kamu usulkan dan kenapa.

Jangan menulis langsung. Bila instruksi tak butuh perubahan, jangan panggil note_write.
"""


def build_editor_agent() -> Agent:
    """Editor (LLM + tool `note_write`) — tidak butuh deps (draft tidak menyentuh DB)."""
    return Agent(build_model(), system_prompt=EDIT_PROMPT, tools=[note_write])


async def propose(note: Note, instruction: str, session: Session) -> tuple[str, dict | None]:
    """Jalankan editor untuk `note` + `instruction` → (answer, draft). draft None bila tak ada usulan."""
    prompt = (
        f"Note (slug={note.slug}, title={note.title}):\n\n{note.content}\n\n"
        f"Instruksi revisi: {instruction}"
    )
    agent = build_editor_agent()
    result = await agent.run(prompt)
    drafts = extract.extract_drafts(result.all_messages(), session)
    return result.output, drafts[0] if drafts else None