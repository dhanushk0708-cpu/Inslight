"""
INSLIGHT Database Backup & Restore Utility.
Supports consistent online SQLite backups via sqlite3.backup() and restore verification.

Usage (from backend/):
  python scripts/backup_db.py backup
  python scripts/backup_db.py restore --file ./data/backups/inslight_backup_YYYYMMDD_HHMMSS.db
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings


def get_sqlite_path() -> str:
    url = settings.DATABASE_URL
    if not url.startswith("sqlite:///"):
        raise RuntimeError("This script handles SQLite backups. For PostgreSQL, use pg_dump / pg_restore.")
    return url.replace("sqlite:///", "", 1)


def backup_sqlite(backup_dir: str) -> str:
    src_path = get_sqlite_path()
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Database file not found: {src_path}")

    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest_path = os.path.join(backup_dir, f"inslight_backup_{ts}.db")

    src_conn = sqlite3.connect(src_path)
    dest_conn = sqlite3.connect(dest_path)
    try:
        src_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        src_conn.close()

    print(f"[OK] Backup created: {dest_path} ({os.path.getsize(dest_path):,} bytes)")
    return dest_path


def restore_sqlite(backup_file: str) -> None:
    if not os.path.exists(backup_file):
        raise FileNotFoundError(f"Backup file not found: {backup_file}")
    dest_path = get_sqlite_path()
    if os.path.exists(dest_path):
        safety_copy = f"{dest_path}.pre_restore.bak"
        shutil.copy2(dest_path, safety_copy)
        print(f"[INFO] Saved pre-restore safety copy: {safety_copy}")

    src_conn = sqlite3.connect(backup_file)
    dest_conn = sqlite3.connect(dest_path)
    try:
        src_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        src_conn.close()
    print(f"[OK] Database restored from {backup_file} -> {dest_path}")


def main():
    parser = argparse.ArgumentParser(description="INSLIGHT SQLite Backup & Restore")
    sub = parser.add_subparsers(dest="command", required=True)

    b = sub.add_parser("backup", help="Create a consistent SQLite backup")
    b.add_argument("--dir", default="./data/backups", help="Backup output directory")

    r = sub.add_parser("restore", help="Restore SQLite database from a backup file")
    r.add_argument("--file", required=True, help="Path to backup .db file")

    args = parser.parse_args()
    if args.command == "backup":
        backup_sqlite(args.dir)
    elif args.command == "restore":
        restore_sqlite(args.file)


if __name__ == "__main__":
    main()
