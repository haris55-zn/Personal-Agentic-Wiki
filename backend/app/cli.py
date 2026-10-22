"""CLI ringan paw — setup database dan konfigurasi LLM tanpa server.

Pakai:  uv run python -m app.cli migrate
        uv run python -m app.cli set-llm
"""
import argparse
import getpass

from app.core.config import BACKEND_DIR
from app.core.database import create_db_and_tables, engine

ENV_FILE = BACKEND_DIR / ".env"

PROVIDERS = {
    "qwen": {
        "label": "QwenCloud (Qwen)",
        "base_url": "https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1",
        "default_model": "qwen3.8-max",
    },
    "opencode": {
        "label": "OpenCode Go",
        "base_url": "https://opencode.ai/inference/go/openai/v1",
        "default_model": "deepseek-v4-pro",
    },
    "google": {
        "label": "Google AI Studio (Gemini)",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-2.5-flash",
    },
}


def cmd_migrate() -> int:
    """Buat tabel bila belum ada; connect bila sudah ada (tak sentuh data lama)."""
    create_db_and_tables()
    print(f"Database siap: {engine.url}")
    return 0


def _update_env(updates: dict[str, str]) -> str:
    """Tulis/timpa key di `.env` tanpa menghapus baris lain."""
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        if key in updates:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")
    return str(ENV_FILE)


def cmd_set_llm() -> int:
    """Dialog: pilih provider → token → simpan ke `.env`."""
    keys = list(PROVIDERS)
    print("Pilih provider:")
    for i, k in enumerate(keys, 1):
        print(f"  {i}. {PROVIDERS[k]['label']}")
    try:
        key = keys[int(input("> ").strip()) - 1]
    except (ValueError, IndexError):
        print("Pilihan tidak valid.")
        return 1
    prov = PROVIDERS[key]

    base_url = input(f"Base URL [{prov['base_url']}]: ").strip() or prov["base_url"]
    model = input(f"Model [{prov['default_model']}]: ").strip() or prov["default_model"]
    token = getpass.getpass("Token (tidak tampil): ").strip()
    if not token:
        print("Token kosong — dibatalkan.")
        return 1

    path = _update_env({"LLM_BASE_URL": base_url, "LLM_API_KEY": token, "LLM_MODEL": model})
    print(f"Tersimpan ke {path}:  LLM_BASE_URL, LLM_API_KEY (tersembunyi), LLM_MODEL={model}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="paw", description="CLI setup paw")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate", help="buat tabel jika belum ada (create/connect)")
    sub.add_parser("set-llm", help="pilih provider LLM + simpan token ke .env")
    args = parser.parse_args(argv)

    if args.command == "migrate":
        return cmd_migrate()
    if args.command == "set-llm":
        return cmd_set_llm()
    parser.error(f"perintah tidak dikenal: {args.command!r}")
    return 1  # tak tercapai


if __name__ == "__main__":
    raise SystemExit(main())