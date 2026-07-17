#!/usr/bin/env python3
"""Build / rebuild a SQLite FTS5 (trigram) index over Markdown notes.

stdlib only — suitable for low-RAM machines (no embeddings, no Docker).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def default_paths() -> tuple[Path, Path]:
    root = Path(__file__).resolve().parent.parent
    return root / "kb", root / "data" / "kb.sqlite"


def parse_note(path: Path, root: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = path.relative_to(root).as_posix()
    title = path.stem
    tags: list[str] = []
    body = text

    fm = FRONT_MATTER_RE.match(text)
    if fm:
        body = text[fm.end() :]
        for line in fm.group(1).splitlines():
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key, val = key.strip().lower(), val.strip().strip("\"'")
            if key == "title" and val:
                title = val
            elif key == "tags" and val:
                tags = [t.strip() for t in re.split(r"[,，]", val) if t.strip()]

    m = TITLE_RE.search(body)
    if m and title == path.stem:
        title = m.group(1).strip()

    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    return {
        "path": rel,
        "title": title,
        "tags": " ".join(tags),
        "body": body.strip(),
        "mtime": mtime,
        "hash": digest,
    }


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS notes (
            path TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL,
            mtime TEXT NOT NULL,
            hash TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
            path UNINDEXED,
            title,
            tags,
            body,
            content='notes',
            content_rowid='rowid',
            tokenize='trigram'
        );

        CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
            INSERT INTO notes_fts(rowid, path, title, tags, body)
            VALUES (new.rowid, new.path, new.title, new.tags, new.body);
        END;

        CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
            INSERT INTO notes_fts(notes_fts, rowid, path, title, tags, body)
            VALUES ('delete', old.rowid, old.path, old.title, old.tags, old.body);
        END;

        CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
            INSERT INTO notes_fts(notes_fts, rowid, path, title, tags, body)
            VALUES ('delete', old.rowid, old.path, old.title, old.tags, old.body);
            INSERT INTO notes_fts(rowid, path, title, tags, body)
            VALUES (new.rowid, new.path, new.title, new.tags, new.body);
        END;
        """
    )
    conn.commit()


def iter_markdown(kb_root: Path):
    for path in sorted(kb_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".mdx", ".txt"}:
            continue
        if any(part.startswith(".") for part in path.relative_to(kb_root).parts):
            continue
        yield path


def rebuild(kb_root: Path, db_path: Path) -> dict:
    kb_root = kb_root.resolve()
    if not kb_root.is_dir():
        raise SystemExit(f"kb root not found: {kb_root}")

    conn = connect(db_path)
    try:
        init_schema(conn)
        existing = {
            row["path"]: row["hash"]
            for row in conn.execute("SELECT path, hash FROM notes")
        }
        seen: set[str] = set()
        added = updated = unchanged = 0

        for path in iter_markdown(kb_root):
            note = parse_note(path, kb_root)
            seen.add(note["path"])
            old_hash = existing.get(note["path"])
            if old_hash == note["hash"]:
                unchanged += 1
                continue
            if old_hash is None:
                conn.execute(
                    "INSERT INTO notes(path, title, tags, body, mtime, hash) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        note["path"],
                        note["title"],
                        note["tags"],
                        note["body"],
                        note["mtime"],
                        note["hash"],
                    ),
                )
                added += 1
            else:
                conn.execute(
                    "UPDATE notes SET title=?, tags=?, body=?, mtime=?, hash=? "
                    "WHERE path=?",
                    (
                        note["title"],
                        note["tags"],
                        note["body"],
                        note["mtime"],
                        note["hash"],
                        note["path"],
                    ),
                )
                updated += 1

        deleted = 0
        for path in set(existing) - seen:
            conn.execute("DELETE FROM notes WHERE path=?", (path,))
            deleted += 1

        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO meta(key, value) VALUES('kb_root', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(kb_root),),
        )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES('indexed_at', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (now,),
        )
        conn.commit()
        total = conn.execute("SELECT COUNT(*) AS c FROM notes").fetchone()["c"]
        return {
            "kb_root": str(kb_root),
            "db_path": str(db_path),
            "total": total,
            "added": added,
            "updated": updated,
            "deleted": deleted,
            "unchanged": unchanged,
            "indexed_at": now,
        }
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    kb_default, db_default = default_paths()
    parser = argparse.ArgumentParser(description="Index Markdown notes into SQLite FTS5")
    parser.add_argument("--kb", type=Path, default=Path(os.environ.get("PERSONAL_KB_ROOT", kb_default)))
    parser.add_argument("--db", type=Path, default=Path(os.environ.get("PERSONAL_KB_DB", db_default)))
    args = parser.parse_args(argv)
    stats = rebuild(args.kb, args.db)
    print(
        f"indexed {stats['total']} notes "
        f"(+{stats['added']} ~{stats['updated']} -{stats['deleted']} "
        f"={stats['unchanged']}) -> {stats['db_path']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
