"""Titik masuk aplikasi FastAPI — jalankan: `uvicorn app.main:app`."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import create_db_and_tables
from app.notes.router import router as notes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Siapkan DB (buat tabel bila belum ada) sekali saat server start — idempotent.
    create_db_and_tables()
    yield


app = FastAPI(title="paw backend", lifespan=lifespan)
app.include_router(notes_router)