"""Vector store Chroma — simpan, hapus, dan cari chunk note."""
import chromadb

from app.core.config import settings
from app.search.chunking import Chunk

COLLECTION_NAME = "note_chunks"

# Klien Chroma (malas: dibuat saat pertama dipakai agar import tak buka DB).
_client = None  # chromadb.PersistentClient


def _get_collection():
    """Koleksi chunk (dibuat bila belum ada). Metrik `cosine` wajib."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(settings.chroma_path))
    return _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def index_note(
    note_id: int,
    slug: str,
    title: str,
    chunks: list[Chunk],
    embeddings: list[list[float]],
) -> None:
    """Timpa semua chunk `note_id` lalu sisipkan yang baru (id stabil)."""
    col = _get_collection()
    col.delete(where={"note_id": note_id})
    if not chunks:
        return
    col.add(
        ids=[f"{note_id}:{i}" for i in range(len(chunks))],
        embeddings=embeddings,
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "note_id": note_id,
                "slug": slug,
                "title": title,
                "heading_path": c.heading_path,
                "anchor": c.anchor,
            }
            for c in chunks
        ],
    )


def delete_note(note_id: int) -> None:
    """Hapus semua chunk milik `note_id`."""
    _get_collection().delete(where={"note_id": note_id})


def search(query_vec: list[float], limit: int) -> list[dict]:
    """Kembalikan `limit` hasil terdekat (distance cosine, makin kecil makin mirip)."""
    col = _get_collection()
    if col.count() == 0:
        return []
    res = col.query(
        query_embeddings=[query_vec],
        n_results=limit,
        include=["documents", "metadatas", "distances"],
    )
    ids = res.get("ids", [[]])[0]
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    out: list[dict] = []
    for i in range(len(ids)):
        meta = metas[i] if i < len(metas) else {}
        out.append({
            "slug": meta.get("slug", ""),
            "title": meta.get("title", ""),
            "heading_path": meta.get("heading_path", "-"),
            "anchor": meta.get("anchor", ""),
            "text": docs[i] if i < len(docs) else "",
            "distance": dists[i] if i < len(dists) else 1.0,
        })
    return out