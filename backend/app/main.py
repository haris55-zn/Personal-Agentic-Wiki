"""Titik masuk aplikasi FastAPI — jalankan: `uvicorn app.main:app`."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.chat.router import router as chat_router
from app.core.database import create_db_and_tables
from app.edits.router import router as editor_router
from app.notes.router import router as notes_router
from app.search.router import router as search_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Siapkan DB (buat tabel bila belum ada) sekali saat server start — idempotent.
    create_db_and_tables()
    yield


app = FastAPI(title="paw backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router)
app.include_router(editor_router)
app.include_router(notes_router)
app.include_router(search_router)