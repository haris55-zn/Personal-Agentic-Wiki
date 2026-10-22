"""Endpoint REST catatan — cocok dengan `frontend/src/lib/api/notes.ts`."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Field, Session, SQLModel

from app.core.database import get_session
from app.notes import crud


# --- bentuk JSON API (dipisah dari tabel di models.py) ---
class NoteInput(SQLModel):
    """Body kiriman POST/PUT: hanya `title`, `content`, `tags`."""
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)


class NoteRead(SQLModel):
    """Bentuk JSON yang dikirim ke frontend (== tipe `Note` TS, tanpa `id` internal)."""
    slug: str
    title: str
    content: str
    type: str
    tags: list[str]
    status: str
    source: str | None
    created_at: datetime
    updated_at: datetime


router = APIRouter(prefix="/api/notes", tags=["notes"])


def _or_404(note, slug: str):
    if note is None:
        raise HTTPException(status_code=404, detail=f"note '{slug}' tidak ditemukan")
    return note


@router.get("", response_model=list[NoteRead])
def list_notes(limit: int = Query(50, ge=1, le=500), session: Session = Depends(get_session)):
    return crud.list_notes(session, limit)


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(body: NoteInput, session: Session = Depends(get_session)):
    return crud.create_note(session, body.title, body.content, body.tags)


@router.get("/{slug}/backlinks", response_model=list[NoteRead])
def get_backlinks(slug: str, session: Session = Depends(get_session)):
    return crud.get_backlinks(session, slug)


@router.get("/{slug}", response_model=NoteRead)
def get_note(slug: str, session: Session = Depends(get_session)):
    return _or_404(crud.get_note(session, slug), slug)


@router.put("/{slug}", response_model=NoteRead)
def update_note(slug: str, body: NoteInput, session: Session = Depends(get_session)):
    return _or_404(crud.update_note(session, slug, body.title, body.content, body.tags), slug)


@router.delete("/{slug}")
def delete_note(slug: str, session: Session = Depends(get_session)):
    if not crud.delete_note(session, slug):
        raise HTTPException(status_code=404, detail=f"note '{slug}' tidak ditemukan")
    return {"deleted": slug}