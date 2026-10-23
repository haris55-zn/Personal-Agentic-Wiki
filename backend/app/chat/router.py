"""Endpoint chat: SSE streaming + riwayat & sesi — cocok `frontend/src/lib/api/chat.ts`.

BELAJAR — SSE (Server-Sent Events):
  POST /api/chat tidak balas JSON sekali jadi; ia balas `text/event-stream`
  dengan bingkai `data: {json}\n\n` yang mengalir SELAMA agen bekerja. Jadi UI
  bisa menggambar jejak ReAct + jawaban SETAHAP demi setahap, bukan menunggu
  selesai semua. Di backend = `StreamingResponse` yang membaca async generator.
"""
import json
import logging
from datetime import datetime
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic_ai.exceptions import UserError
from sqlmodel import SQLModel, Session, select

from app.chat.agent import build_agent, stream_events
from app.chat.models import ChatMessage, ChatSession
from app.core.database import get_session
from app.notes.models import utcnow

_log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(SQLModel):
    """Body POST /api/chat (persis `{session_id, message}` dari chat.ts)."""
    session_id: str
    message: str


class ChatSessionRead(SQLModel):
    """Bentuk sesi ke frontend (== tipe TS `ChatSession`: tanpa created_at)."""
    id: str
    title: str
    updated_at: datetime


class ChatMessageRead(SQLModel):
    """Bentuk pesan ke frontend (== tipe TS `ChatMessage`: role + content)."""
    role: str
    content: str


def _get_or_create_session(session: Session, session_id: str, message: str) -> ChatSession:
    """Ambil sesi, atau buat baru dengan judul = pesan user pertama."""
    cs = session.get(ChatSession, session_id)
    if cs is None:
        cs = ChatSession(id=session_id, title=message)
        session.add(cs)
    return cs


def _append_message(session: Session, session_id: str, role: str, content: str) -> None:
    session.add(ChatMessage(session_id=session_id, role=role, content=content))


def _touch(session: Session, session_id: str) -> None:
    """Cap updated_at agar sesi naik ke atas daftar Recent Chat."""
    cs = session.get(ChatSession, session_id)
    if cs is not None:
        cs.updated_at = utcnow()
        session.add(cs)


async def _sse(message: str, session: Session, session_id: str) -> AsyncIterator[str]:
    """Teruskan event agen sebagai bingkai SSE, lalu simpan jawaban asisten."""
    answer: list[str] = []
    try:
        async for ev in stream_events(message, session):
            if ev.get("event") == "answer":
                answer.append(ev["content"])
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
    except Exception as exc:  # kesalahan runtime (network LLM dll) → tutup dgn jawaban error
        _log.exception("agen gagal sesi %s", session_id)
        answer.append(f"Maaf, terjadi kesalahan: {exc}")
        yield f"data: {json.dumps({'event': 'answer', 'content': answer[0]}, ensure_ascii=False)}\n\n"
    finally:
        _append_message(session, session_id, "assistant", "".join(answer))
        _touch(session, session_id)
        session.commit()


@router.post("")
async def chat(body: ChatRequest, session: Session = Depends(get_session)):
    # Validasi agen LEBIH AWAL: begitu header SSE terkirim, status 200 tak bisa
    # berubah jadi 4xx. Jadi `UserError` (LLM belum di-set-llm) harus ketangkap
    # SEBELUM StreamingResponse dikembalikan.
    try:
        build_agent()
    except UserError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM belum dikonfigurasi — jalankan `uv run paw-cli set-llm` dulu",
        ) from exc

    _get_or_create_session(session, body.session_id, body.message)
    _append_message(session, body.session_id, "user", body.message)
    _touch(session, body.session_id)
    session.commit()

    return StreamingResponse(
        _sse(body.message, session, body.session_id),
        media_type="text/event-stream",
    )


@router.get("/sessions", response_model=list[ChatSessionRead])
def list_sessions(session: Session = Depends(get_session)):
    rows = session.exec(select(ChatSession).order_by(ChatSession.updated_at.desc()))
    return list(rows)


@router.get("/history/{session_id}", response_model=list[ChatMessageRead])
def history(session_id: str, session: Session = Depends(get_session)):
    rows = session.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id)
    )
    return list(rows)


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, session: Session = Depends(get_session)):
    cs = session.get(ChatSession, session_id)
    if cs is None:
        raise HTTPException(status_code=404, detail=f"sesi '{session_id}' tidak ditemukan")
    for m in session.exec(select(ChatMessage).where(ChatMessage.session_id == session_id)):
        session.delete(m)
    session.delete(cs)
    session.commit()
    return {"deleted": session_id}