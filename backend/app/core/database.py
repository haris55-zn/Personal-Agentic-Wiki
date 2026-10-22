"""Engine database + sesi SQLModel (SQLite, berupa satu file)."""
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

# Koneksi SQLite lewat SQLAlchemy (dipakai SQLModel).
engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False},  # FastAPI jalankan handler di threadpool
)


def create_db_and_tables() -> None:
    """Buat folder `data/` (bila belum ada) + seluruh tabel terdaftar di metadata."""
    # Import model dulu agar tabelnya terdaftar di SQLModel.metadata sebelum `create_all`.
    import app.notes.models  # noqa: F401  (sisi-efek: daftarkan tabel Note/NoteChunk)

    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency FastAPI: buka sesi DB, tutup otomatis setelah tiap request."""
    with Session(engine) as session:
        yield session