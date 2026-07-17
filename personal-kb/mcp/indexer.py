#!/usr/bin/env python3
"""Build / rebuild a SQLite FTS5 (trigram) index over Markdown notes.

Supports multiple source roots (in-place indexing — no file copy).
stdlib only — suitable for low-RAM machines.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from config import default_db_path, default_paths_compat, load_config

# re-export for older imports
def default_paths() -> tuple[Path, Path]:
    return default_paths_compat()


FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def parse_note(
    path: Path,
    *,
    root_id: str,
    root_path: Path,
) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = path.relative_to(root_path).as_posix()
    logical = f"{root_id}/{rel}"
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
        "path": logical,
        "root_id": root_id,
        "rel_path": rel,
        "abs_path": str(path.resolve()),
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


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS notes (
            path TEXT PRIMARY KEY,
            root_id TEXT NOT NULL DEFAULT 'notes',
            rel_path TEXT NOT NULL DEFAULT '',
            abs_path TEXT NOT NULL DEFAULT '',
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
        """
    )

    # Migrate older DBs that lack multi-root columns
    cols = _table_columns(conn, "notes")
    for col, decl in (
        ("root_id", "TEXT NOT NULL DEFAULT 'notes'"),
        ("rel_path", "TEXT NOT NULL DEFAULT ''"),
        ("abs_path", "TEXT NOT NULL DEFAULT ''"),
    ):
        if col not in cols:
            conn.execute(f"ALTER TABLE notes ADD COLUMN {col} {decl}")

    # Triggers (drop+recreate so upgrades are safe)
    conn.executescript(
        """
        DROP TRIGGER IF EXISTS notes_ai;
        DROP TRIGGER IF EXISTS notes_ad;
        DROP TRIGGER IF EXISTS notes_au;

        CREATE TRIGGER notes_ai AFTER INSERT ON notes BEGIN
            INSERT INTO notes_fts(rowid, path, title, tags, body)
            VALUES (new.rowid, new.path, new.title, new.tags, new.body);
        END;

        CREATE TRIGGER notes_ad AFTER DELETE ON notes BEGIN
            INSERT INTO notes_fts(notes_fts, rowid, path, title, tags, body)
            VALUES ('delete', old.rowid, old.path, old.title, old.tags, old.body);
        END;

        CREATE TRIGGER notes_au AFTER UPDATE ON notes BEGIN
            INSERT INTO notes_fts(notes_fts, rowid, path, title, tags, body)
            VALUES ('delete', old.rowid, old.path, old.title, old.tags, old.body);
            INSERT INTO notes_fts(rowid, path, title, tags, body)
            VALUES (new.rowid, new.path, new.title, new.tags, new.body);
        END;
        """
    )
    conn.commit()


def _should_skip_dir(name: str, exclude: set[str]) -> bool:
    if name.startswith(".") and name not in {".", ".."}:
        # keep hidden dirs out by default (except we already list common ones)
        return True
    return name in exclude


def iter_documents(
    root_path: Path,
    *,
    extensions: Iterable[str],
    exclude_dirs: set[str],
):
    exts = {e.lower() for e in extensions}
    if not root_path.is_dir():
        return
    stack = [root_path]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in sorted(entries, key=lambda p: p.name.lower()):
            try:
                if entry.is_dir():
                    if _should_skip_dir(entry.name, exclude_dirs):
                        continue
                    stack.append(entry)
                elif entry.is_file():
                    if entry.suffix.lower() in exts:
                        yield entry
            except OSError:
                continue


def rebuild_from_config(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    db_path: Path = cfg["db_path"]
    roots = cfg["roots"]
    if not roots:
        raise SystemExit("no roots configured")

    conn = connect(db_path)
    try:
        init_schema(conn)
        existing = {
            row["path"]: (row["hash"], row["abs_path"] if "abs_path" in row.keys() else "")
            for row in conn.execute("SELECT path, hash, abs_path FROM notes")
        }
        seen: set[str] = set()
        added = updated = unchanged = 0
        skipped_roots: list[str] = []
        per_root: dict[str, int] = {}

        for root in roots:
            root_id = root["id"]
            root_path: Path = root["path"]
            if not root_path.is_dir():
                skipped_roots.append(f"{root_id}:{root_path}")
                continue
            count_here = 0
            for path in iter_documents(
                root_path,
                extensions=cfg["include_extensions"],
                exclude_dirs=cfg["exclude_dir_names"],
            ):
                note = parse_note(path, root_id=root_id, root_path=root_path)
                seen.add(note["path"])
                count_here += 1
                old = existing.get(note["path"])
                if old and old[0] == note["hash"]:
                    unchanged += 1
                    continue
                if old is None:
                    conn.execute(
                        "INSERT INTO notes(path, root_id, rel_path, abs_path, title, tags, body, mtime, hash) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            note["path"],
                            note["root_id"],
                            note["rel_path"],
                            note["abs_path"],
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
                        "UPDATE notes SET root_id=?, rel_path=?, abs_path=?, title=?, tags=?, "
                        "body=?, mtime=?, hash=? WHERE path=?",
                        (
                            note["root_id"],
                            note["rel_path"],
                            note["abs_path"],
                            note["title"],
                            note["tags"],
                            note["body"],
                            note["mtime"],
                            note["hash"],
                            note["path"],
                        ),
                    )
                    updated += 1
            per_root[root_id] = count_here

        deleted = 0
        for path in set(existing) - seen:
            conn.execute("DELETE FROM notes WHERE path=?", (path,))
            deleted += 1

        now = datetime.now(timezone.utc).isoformat()
        roots_meta = [
            {"id": r["id"], "path": str(r["path"]), "description": r.get("description") or ""}
            for r in roots
        ]
        conn.execute(
            "INSERT INTO meta(key, value) VALUES('roots', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (json.dumps(roots_meta, ensure_ascii=False),),
        )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES('indexed_at', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (now,),
        )
        conn.commit()
        total = conn.execute("SELECT COUNT(*) AS c FROM notes").fetchone()["c"]
        return {
            "db_path": str(db_path),
            "roots": roots_meta,
            "per_root": per_root,
            "skipped_roots": skipped_roots,
            "total": total,
            "added": added,
            "updated": updated,
            "deleted": deleted,
            "unchanged": unchanged,
            "indexed_at": now,
            "mode": "in-place (no copy)",
        }
    finally:
        conn.close()


def rebuild(kb_root: Path | None = None, db_path: Path | None = None) -> dict[str, Any]:
    """Backward-compatible entry: single root or full config."""
    if kb_root is None and db_path is None:
        return rebuild_from_config()
    cfg = load_config()
    if db_path is not None:
        cfg["db_path"] = Path(db_path)
    if kb_root is not None:
        cfg["roots"] = [
            {
                "id": "notes",
                "path": Path(kb_root).expanduser().resolve(),
                "description": "legacy --kb",
                "enabled": True,
            }
        ]
    return rebuild_from_config(cfg)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Index Markdown notes into SQLite FTS5 (multi-root, in-place)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config.json (default: personal-kb/config.json)",
    )
    parser.add_argument(
        "--kb",
        type=Path,
        default=None,
        help="Legacy: index a single root (overrides config roots)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite db path (default from config / env)",
    )
    args = parser.parse_args(argv)

    if args.config is not None:
        os.environ["PERSONAL_KB_CONFIG"] = str(args.config)

    if args.kb is not None:
        stats = rebuild(args.kb, args.db or load_config()["db_path"])
    else:
        cfg = load_config()
        if args.db is not None:
            cfg["db_path"] = Path(args.db)
        stats = rebuild_from_config(cfg)

    print(
        f"indexed {stats['total']} docs "
        f"(+{stats['added']} ~{stats['updated']} -{stats['deleted']} "
        f"={stats['unchanged']}) roots={list(stats.get('per_root', {}))} "
        f"-> {stats['db_path']}"
    )
    if stats.get("skipped_roots"):
        print("skipped missing roots:", ", ".join(stats["skipped_roots"]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
