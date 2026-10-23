"""Tool edit agent: `note_write` — MENGUSUL (bukan menulis) perubahan note.

Dibagi ke chat agent (inline draft) DAN editor agent (propose). Tool ini TIDAK
menyentuh DB — ia cuma mengembalikan string ACK (observation); draft asli
dipulihkan backend dari `ToolCallPart.args` (lihat `edits.extract`).
"""
from app.edits.schema import NoteEdit


def note_write(edit: NoteEdit) -> str:
    """Usulkan pembuatan/perubahan note (HANYA draft — belum ditulis; user yang Apply).

    `edit` = draft lengkap: `action` (create/update), `slug`, `title`,
    `content_markdown` (isi penuh baru), `tags`, `source`, `type_`.
    """
    return f"draft '{edit.action}' untuk note '{edit.slug}' disiapkan (belum ditulis)."