# Personal Agentic Wiki (paw)

Wiki pribadi **local-first** + **chat AI**. Catatan ditulis dalam Markdown, dicari & diindeks **secara lokal**; chat AI bisa membaca/mencari catatanmu dan menelusuri web.

## Isi repo

| Folder | Isi |
|---|---|
| `backend/` | API (FastAPI), pencarian vektor (ChromaDB + embedding lokal), chat agent (pydantic-ai) |
| `frontend/` | UI web (SvelteKit + Svelte 5) |

## Prasyarat

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — pengelola paket Python
- **[bun](https://bun.sh)** — runtime JavaScript

## Menjalankan

```bash
# 1) clone
git clone https://github.com/haris55-zn/Personal-Agentic-Wiki.git
cd Personal-Agentic-Wiki

# 2) backend — terminal 1
cd backend
uv sync                                  # install dependensi
cp .env.example .env                     # isi LLM_API_KEY & LLM_BASE_URL (wajib utk chat)
uv run uvicorn app.main:app --reload     # → http://localhost:8000

# 3) frontend — terminal 2
cd frontend
bun install                              # install dependensi
bun run dev                              # → http://localhost:5173
```

Buka **http://localhost:5173**.

## Konfigurasi LLM (agar chat jalan)

Chat butuh model OpenAI-compatible. Isi `backend/.env`:

```env
LLM_API_KEY=sk-...
LLM_BASE_URL=https://.../compatible-mode/v1
LLM_MODEL=deepseek-v4-pro
```

atau lewat dialog interaktif:

```bash
cd backend
uv run paw-cli set-llm
```

Tanpa LLM, catatan + pencarian tetap jalan; hanya **chat** yang butuh key.