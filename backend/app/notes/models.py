"""Tabel database (SQLModel) untuk catatan — TERPISAH dari operasi CRUD."""
from datetime import datetime, timezone

from sqlmodel import JSON, Column, Field, SQLModel


def utcnow() -> datetime:
    """Waktu UTC sekarang, naive (SQLite tak menyimpan zona waktu)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Note(SQLModel, table=True):
    """Satu catatan wiki. `id` = PK internal; `slug` unik & bisa berubah saat ganti judul."""

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True)
    title: str
    content: str
    type: str = "note"
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = "published"
    source: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class NoteChunk(SQLModel, table=True):
    """Potongan teks catatan untuk pencarian semantik (dipakai Fase 2)."""

    id: int | None = Field(default=None, primary_key=True)
    note_id: int = Field(foreign_key="note.id", index=True)
    chunk_index: int
    content: str
    heading_path: str | None = None