"""Skema draft edit — dipakai LLM (arg tool) dan respons API.

BELAJAR — dua model yang berbeda peran:
  - `NoteEdit` (pydantic `BaseModel`) = argumen tool. Pydantic-ai mengubahnya
    jadi JSON Schema yang dikirim ke LLM; LLM WAJIB mengisi field ini saat
    memanggil `note_write`. Catatan: `part.args` bisa `dict` ATAU string JSON
    mentah (tergantung provider) — normalisasi dulu sebelum `NoteEdit(**args)`.
  - `DraftOut` (SQLModel) = bentuk draft yang dikirim ke frontend, DITAMBAH
    `diff` + `preview` yang dihitung backend (bukan dari LLM).
"""
from typing import Literal

from pydantic import BaseModel, Field
from sqlmodel import SQLModel


class NoteEdit(BaseModel):
    """Draft edit yang diisi LLM. Bukan perintah tulis — hanya usulan."""
    action: Literal['create', 'update']
    slug: str            # create → slug baru; update → slug note yang diubah
    title: str
    content_markdown: str  # isi PENUH versi baru (markdown)
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    type_: str = 'note'


class DraftOut(SQLModel):
    """Bentuk draft ke frontend (== tipe TS `Draft`): + `diff` & `preview`."""
    action: str
    slug: str
    title: str
    content_markdown: str
    tags: list[str]
    source: str | None
    type_: str
    diff: str
    preview: str