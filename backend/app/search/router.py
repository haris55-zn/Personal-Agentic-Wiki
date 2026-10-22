"""Endpoint pencarian — cocok dengan `frontend/src/lib/api/search.ts`."""
from fastapi import APIRouter, Query

from app.search.service import SearchResult, search_wiki

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
def search(q: str = Query(""), limit: int = Query(12, ge=1, le=50)):
    """GET /api/search?q=...&limit=... → hasil ranked + snippet + anchor."""
    return search_wiki(q, limit)