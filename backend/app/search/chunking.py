"""Pecah markdown note jadi chunk per-heading, untuk indexing search."""
import re
from dataclasses import dataclass

from app.notes.crud import slugify

# Heading ATX: `#`/`##`/… + spasi + teks. Penutup `##` opsional (didahului spasi).
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_TRAILING_HASH = re.compile(r"\s+#+\s*$")


@dataclass
class Chunk:
    """Satu bagian note (di bawah satu heading) siap di-embed."""
    note_id: int
    slug: str
    title: str
    heading_path: str   # "Induk › Anak"; "-" bila tanpa heading
    anchor: str         # slug heading terdalam; "" bila tanpa heading
    text: str           # isi bagian (untuk embed + snippet)


def _heading_text(raw: str) -> str:
    """Buang penutup ATX `#` (mis. `Intro ##` → `Intro`) tanpa makan `C#`."""
    return _TRAILING_HASH.sub("", raw).strip()


def _make_chunk(note, stack: list[tuple[int, str]], body: list[str]) -> Chunk | None:
    text = "\n".join(body).strip()
    if not text:
        return None
    if stack:
        heading_path = " › ".join(h for _, h in stack)
        anchor = slugify(stack[-1][1])
    else:
        heading_path = "-"
        anchor = ""
    return Chunk(note.id, note.slug, note.title, heading_path, anchor, text)


def chunk_note(note) -> list[Chunk]:
    """Belah `note.content` per heading markdown; return chunk non-kosong."""
    stack: list[tuple[int, str]] = []
    chunks: list[Chunk] = []
    body: list[str] = []

    def flush() -> None:
        chunk = _make_chunk(note, stack, body)
        body.clear()
        if chunk:
            chunks.append(chunk)

    for line in note.content.splitlines():
        m = _HEADING_RE.match(line)
        if not m:
            body.append(line)
            continue
        heading = _heading_text(m.group(2))
        if not heading:
            body.append(line)  # "## ###" — bukan heading sungguhan
            continue
        flush()  # tutup seksi lama (pakai stack lama)
        level = len(m.group(1))
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, heading))
    flush()
    return chunks