"""Fitur edit agentic: agen MENGUSUL draft (`note_write`), tak menulis.

GERBANG KEAMANAN: draft hanya proposal; satu-satunya jalur tulis adalah
`POST /api/notes/apply-diff`, dipicu tombol "Apply" user — tak ada tulis otomatis.
"""