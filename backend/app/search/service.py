"""Orkestrasi pencarian: chunk+embed+indeks, susun SearchResult + snippet."""
import re

from sqlmodel import SQLModel

from app.notes.models import Note
from app.search import store
from app.search.chunking import chunk_note
from app.search.embeddings import embed_query, embed_passages


class SearchResult(SQLModel):
    """Bentuk JSON hasil search (== tipe `SearchResult` TS)."""
    rank: int
    slug: str
    title: str
    heading_path: str
    anchor: str
    snippet: str
    score: float


def make_snippet(text: str, query: str) -> str:
    """Jendela teks (~120 char) di sekitar kemunculan pertama kata kunci."""
    flat = re.sub(r"\s+", " ", text).strip()
    needle = query.strip().lower()
    pos = flat.lower().find(needle) if needle else 0
    if pos == -1:
        pos = 0
    start = max(0, pos - 20)
    end = pos + 100
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(flat) else ""
    return prefix + flat[start:end] + suffix


def _to_result(rank: int, hit: dict, query: str) -> SearchResult:
    return SearchResult(
        rank=rank,
        slug=hit["slug"],
        title=hit["title"],
        heading_path=hit["heading_path"],
        anchor=hit["anchor"],
        snippet=make_snippet(hit["text"], query),
        score=round(1.0 - hit["distance"], 4),
    )


def search_wiki(query: str, limit: int) -> list[SearchResult]:
    """Cari chunk terdekat → SearchResult. Kueri < 2 char → kosong (== dummy.ts)."""
    if len(query.strip()) < 2:
        return []
    hits = store.search(embed_query(query), limit)
    return [_to_result(i, hit, query) for i, hit in enumerate(hits, 1)]


def reindex_note(note: Note) -> None:
    """(Bongkar) chunk + embed + simpan indeks untuk satu note."""
    chunks = chunk_note(note)
    if not chunks:
        store.delete_note(note.id)
        return
    store.index_note(
        note.id, note.slug, note.title, chunks, embed_passages([c.text for c in chunks])
    )


def remove_note(note_id: int) -> None:
    """Hapus note dari indeks."""
    store.delete_note(note_id)