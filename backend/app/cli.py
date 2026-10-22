"""CLI ringan paw — setup database tanpa menjalankan server.

Pakai:  uv run python -m app.cli migrate
"""
import argparse

from app.core.database import create_db_and_tables, engine


def cmd_migrate() -> int:
    """Buat tabel bila belum ada; connect bila sudah ada (tak sentuh data lama)."""
    create_db_and_tables()
    print(f"Database siap: {engine.url}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="paw", description="CLI setup paw")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate", help="buat tabel jika belum ada (create/connect)")
    args = parser.parse_args(argv)

    if args.command == "migrate":
        return cmd_migrate()
    parser.error(f"perintah tidak dikenal: {args.command!r}")
    return 1  # tak tercapai


if __name__ == "__main__":
    raise SystemExit(main())