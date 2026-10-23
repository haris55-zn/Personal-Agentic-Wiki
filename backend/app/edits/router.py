"""Endpoint editor: POST /api/editor/propose → usulan edit (answer + draft)."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic_ai.exceptions import UserError
from sqlmodel import SQLModel, Session

from app.core.database import get_session
from app.edits import agent as editor_agent
from app.edits.schema import DraftOut
from app.notes import crud

_log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/editor", tags=["editor"])


class ProposeBody(SQLModel):
    """Body POST /propose (persis dari `chat.ts` `proposeEdit`)."""
    slug: str
    instruction: str
    session_id: str = ""  # diterima tapi belum dipakai (v1: propose tidak menulis riwayat)


class ProposeResult(SQLModel):
    """Respons (== tipe TS `ProposeResult`)."""
    slug: str
    instruction: str
    answer: str
    draft: DraftOut | None = None


@router.post("/propose", response_model=ProposeResult)
async def propose(body: ProposeBody, session: Session = Depends(get_session)):
    note = crud.get_note(session, body.slug)
    if note is None:
        raise HTTPException(status_code=404, detail=f"note '{body.slug}' tidak ditemukan")

    try:
        editor_agent.build_editor_agent()  # fail-fast: LLM belum di-set-llm → 400
    except UserError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM belum dikonfigurasi — jalankan `uv run paw-cli set-llm` dulu",
        ) from exc

    answer, draft = await editor_agent.propose(note, body.instruction, session)
    return ProposeResult(
        slug=body.slug, instruction=body.instruction, answer=answer, draft=draft
    )