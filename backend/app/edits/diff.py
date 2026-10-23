"""Hitung `diff` & `preview` draft — deterministik (bukan dari LLM).

Kenapa dihitung di sini, bukan diminta LLM:
  `content_markdown` = isi baru yang diusul LLM. `diff` = SELISIH lama→baru;
  ini komputasi deterministik, jadi lebih andal dihitung Python (difflib)
  daripada berharap LLM menulis diff yang benar.
"""
import difflib

from app.edits.schema import NoteEdit


def make_diff(old: str | None, new: str, slug: str) -> str:
    """Unified diff lama→baru. `old=None` (create) → semua baris ditandai `+`."""
    new_lines = new.splitlines()
    if old is None:
        return "\n".join(f"+ {line}" for line in new_lines)
    return "\n".join(
        difflib.unified_diff(
            old.splitlines(), new_lines,
            fromfile=f"a/{slug}", tofile=f"b/{slug}", lineterm="",
        )
    )


def make_preview(edit: NoteEdit) -> str:
    """Ringkasan satu baris untuk baris `preview` di DiffPanel."""
    verb = "Membuat" if edit.action == "create" else "Mengubah"
    return f"{verb} note '{edit.slug}'"