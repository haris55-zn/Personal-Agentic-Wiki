"""Engine database + sesi SQLModel — SQLite (bawaan) atau Postgres via `DATABASE_URL`."""
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


def _engine_kwargs() -> dict:
    """Opsi tambahan per driver. SQLite butuh `check_same_thread` + folder dibuat dulu."""
    url = make_url(settings.database_url)
    if url.drivername.startswith("sqlite"):
        if url.database and url.database != ":memory:":
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        return {"connect_args": {"check_same_thread": False}}
    return {}  # Postgres/driver lain: tanpa opsi khusus


engine = create_engine(settings.database_url, **_engine_kwargs())


def create_db_and_tables() -> None:
    """Buat seluruh tabel terdaftar bila belum ada (idempotent — tak drop/alter data)."""
    # Import model dulu agar tabelnya terdaftar di SQLModel.metadata sebelum `create_all`.
    import app.notes.models  # noqa: F401  (sisi-efek: daftarkan tabel Note/NoteChunk)

    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency FastAPI: buka sesi DB, tutup otomatis setelah tiap request."""
    with Session(engine) as session:
        yield session