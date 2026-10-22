# frontend/src/lib/api — klien API backend (:8000)

Fetch langsung ke FastAPI (tanpa server-proxy; CORS dari env FRONTEND_ORIGIN).
Semua panggilan HTTP lewat sini — komponen tidak fetch sendiri.

## Cara menambah klien
1 file `<domain>.ts` + fungsi typed → tambah DTO di `types.ts` bila perlu.

## File
- `client.ts` — API_BASE_URL + apiFetch wrapper + ApiError
- `types.ts` — DTO: Note, ChatMessage, ChatSession, SearchResult, ReactStep
- `notes.ts` — CRUD note, backlinks, apply-diff
- `search.ts` — search mdbook-style
- `chat.ts` — SSE streamChat ReAct (AbortSignal), history, sesi (list/delete), proposeEdit (jawaban + draft)
- `draft.ts` — tipe Draft yang dibagikan chat, sidebar, dan DiffPanel
