"""Tabel database (SQLModel) untuk catatan — TERPISAH dari operasi CRUD."""
from datetime import datetime, timezone

from sqlmodel import JSON, Column, Field, SQLModel


def utcnow() -> datetime:
    """Waktu UTC sekarang (dipakai sebagai default timestamp)."""
    return datetime.now(timezone.utc)


class Note(SQLModel, table=True):
    """Satu catatan wiki; `slug` = identitas unik (dibuat dari judul, di-dedupe di CRUD)."""

    slug: str = Field(primary_key=True)
    title: str
    content: str
    type: str = "note"
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = "active"
    source: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class NoteChunk(SQLModel, table=True):
    """Potongan teks catatan untuk pencarian semantik (dipakai Fase 2)."""

    id: int | None = Field(default=None, primary_key=True)
    note_slug: str = Field(foreign_key="note.slug", index=True)
    chunk_index: int
    content: str
    heading_path: str | None = None