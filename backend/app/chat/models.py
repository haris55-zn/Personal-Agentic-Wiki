"""Tabel riwayat chat: `chatsession` (sesi) dan `chatmessage` (pesan).

BELAJAR — kenapa `ChatSession.id` bertipe STRING, bukan int auto-increment:
  Frontend membuat uuid sesi sendiri lalu mengirim `{session_id}` saat
  POST /api/chat. Backend harus memakai id YANG SAMA supaya riwayat bisa
  disambung antar-refresh/perangkat — tidak ada pemetaan id baru.

BELAJAR — relasi satu-ke-banyak:
  Satu sesi → banyak pesan (`ChatMessage.session_id` FK → `ChatSession.id`).
  Pola persis `NoteChunk` → `Note` di modul notes: cukup simpan FK + index,
  lalu query manual lewat `select(...).where(...)`. `Relationship` SQLModel
  tidak dipakai di sini agar tetap sederhana & mudah ditelusuri pemula.
"""
from datetime import datetime

from sqlmodel import Field, SQLModel

# Import `utcnow` dari notes supaya hanya ADA SATU definisi (hindari duplikasi).
from app.notes.models import utcnow


class ChatSession(SQLModel, table=True):
    """Satu percakapan. Nama tabel otomatis `chatsession` (lowercase class)."""
    id: str = Field(primary_key=True)      # uuid dari client
    title: str                              # pesan user pertama
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)  # dicap di tiap pesan baru


class ChatMessage(SQLModel, table=True):
    """Satu pesan. Nama tabel otomatis `chatmessage`."""
    id: int | None = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="chatsession.id", index=True)
    role: str            # "user" | "assistant" (sesuai tipe TS `ChatMessage.role`)
    content: str
    created_at: datetime = Field(default_factory=utcnow)