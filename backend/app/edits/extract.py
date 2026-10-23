"""Tarik draft dari transkrip pydantic-ai → dict bentuk `DraftOut`.

Jantung alur draft: saat LLM memanggil `note_write`, pydantic-ai menyimpan
`ToolCallPart(args={...})` di `all_messages()`. Kita pindai part itu, ubah
`args` jadi `NoteEdit`, lalu HITUNG `diff` (dari isi lama di DB) + `preview`.
"""
from sqlmodel import Session

from app.edits.diff import make_diff, make_preview
from app.edits.schema import NoteEdit
from app.notes.crud import get_note


def build_draft(edit: NoteEdit, old: str | None) -> dict:
    """Susun dict draft (bentuk `DraftOut`) + hitung `diff` & `preview`."""
    return {
        "action": edit.action,
        "slug": edit.slug,
        "title": edit.title,
        "content_markdown": edit.content_markdown,
        "tags": edit.tags,
        "source": edit.source,
        "type_": edit.type_,
        "diff": make_diff(old, edit.content_markdown, edit.slug),
        "preview": make_preview(edit),
    }


def extract_drafts(messages, session: Session) -> list[dict]:
    """Pindai transkrip; return daftar draft untuk tiap panggilan `note_write`.

    Untuk `action=update`, isi LAMA diambil dari DB supaya `diff` akurat.
    """
    drafts: list[dict] = []
    for message in messages:
        for part in message.parts:
            if getattr(part, "part_kind", None) == "tool-call" and part.tool_name == "note_write":
                edit = NoteEdit(**part.args)
                old = None
                if edit.action == "update":
                    note = get_note(session, edit.slug)
                    old = note.content if note is not None else None
                drafts.append(build_draft(edit, old))
    return drafts