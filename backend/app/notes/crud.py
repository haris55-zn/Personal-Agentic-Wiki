"""Operasi CRUD catatan: slug unik, create/read/update/delete, backlink."""
import re

from sqlmodel import Session, select

from app.notes.models import Note, utcnow


def slugify(title: str) -> str:
    """Ubah judul → slug URL. ATURAN SAMA dengan `dummy.ts` (backend patuh kontrak)."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _slug_exists(session: Session, slug: str) -> bool:
    """True bila sudah ada note dengan `slug` itu."""
    return session.exec(select(Note.slug).where(Note.slug == slug)).first() is not None


def unique_slug(session: Session, base: str, keep: str | None = None) -> str:
    """Slug unik. `keep` = slug milik note ini sendiri (rename tanpa ganti judul)."""
    root = base or "untitled"
    slug = root
    n = 2
    while slug != keep and _slug_exists(session, slug):
        slug = f"{root}-{n}"
        n += 1
    return slug


def list_notes(session: Session, limit: int = 50) -> list[Note]:
    """Note terbaru-dulu (sesuai urutan `unshift` di dummy.ts)."""
    return list(session.exec(select(Note).order_by(Note.created_at.desc()).limit(limit)))


def get_note(session: Session, slug: str) -> Note | None:
    return session.exec(select(Note).where(Note.slug == slug)).first()


def get_backlinks(session: Session, slug: str) -> list[Note]:
    """Note lain yang `content`-nya memuat tautan wiki `[[slug]]` (mirip dummy.ts)."""
    stmt = select(Note).where(Note.content.contains(f"[[{slug}]]"), Note.slug != slug)
    return list(session.exec(stmt))


def create_note(session: Session, title: str, content: str, tags: list[str]) -> Note:
    """Buat note baru. `type`/`status`/`source`/timestamp diisi otomatis dari default model."""
    note = Note(slug=unique_slug(session, slugify(title)), title=title, content=content, tags=tags)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def update_note(
    session: Session, slug: str, title: str, content: str, tags: list[str]
) -> Note | None:
    """Update isi + slug (bisa berubah saat judul diganti). `None` bila slug tak ada."""
    note = get_note(session, slug)
    if note is None:
        return None
    note.title = title
    note.content = content
    note.tags = tags
    note.slug = unique_slug(session, slugify(title), keep=slug)
    note.updated_at = utcnow()
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def delete_note(session: Session, slug: str) -> bool:
    """Hapus note. `True` bila berhasil, `False` bila slug tak ditemukan."""
    note = get_note(session, slug)
    if note is None:
        return False
    session.delete(note)
    session.commit()
    return True