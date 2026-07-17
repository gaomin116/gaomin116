#!/usr/bin/env python3
"""Minimal stdio MCP server for personal Markdown knowledge base.

Tools:
  - kb_search: FTS5 trigram search (Chinese + English friendly)
  - kb_get:    read a note by relative path
  - kb_list:   list notes (optional prefix / limit)
  - kb_stats:  index stats
  - kb_reindex: rebuild index from disk

stdlib only — no pip install required.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

# Allow `python server.py` from any cwd
_MCP_DIR = Path(__file__).resolve().parent
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from indexer import connect, default_paths, init_schema, rebuild  # noqa: E402

SERVER_NAME = "personal-kb"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"


def env_paths() -> tuple[Path, Path]:
    kb_default, db_default = default_paths()
    kb = Path(os.environ.get("PERSONAL_KB_ROOT", kb_default)).expanduser()
    db = Path(os.environ.get("PERSONAL_KB_DB", db_default)).expanduser()
    return kb, db


def ensure_db(db_path: Path, kb_root: Path) -> sqlite3.Connection:
    conn = connect(db_path)
    init_schema(conn)
    count = conn.execute("SELECT COUNT(*) AS c FROM notes").fetchone()["c"]
    if count == 0 and kb_root.is_dir():
        conn.close()
        rebuild(kb_root, db_path)
        conn = connect(db_path)
        init_schema(conn)
    return conn


def snippet(text: str, query: str, radius: int = 80) -> str:
    if not text:
        return ""
    q = query.strip()
    idx = text.lower().find(q.lower()) if q else -1
    if idx < 0:
        # try first CJK / word chunk of query
        for part in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_]{2,}", q):
            idx = text.lower().find(part.lower())
            if idx >= 0:
                break
    if idx < 0:
        flat = re.sub(r"\s+", " ", text).strip()
        return flat[: radius * 2] + ("…" if len(flat) > radius * 2 else "")
    start = max(0, idx - radius)
    end = min(len(text), idx + len(q) + radius)
    piece = re.sub(r"\s+", " ", text[start:end]).strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{piece}{suffix}"


def tool_defs() -> list[dict[str, Any]]:
    return [
        {
            "name": "kb_search",
            "description": (
                "Search the local personal knowledge base (Markdown notes) "
                "using SQLite FTS5 trigram. Good for Chinese and English. "
                "Returns path, title, tags, and a short snippet."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (keywords or phrase)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 8, max 20)",
                        "default": 8,
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "kb_get",
            "description": (
                "Read the full content of a knowledge-base note by its "
                "relative path (as returned by kb_search / kb_list)."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path under kb/, e.g. topics/cursor.md",
                    },
                },
                "required": ["path"],
            },
        },
        {
            "name": "kb_list",
            "description": "List notes in the knowledge base, optionally filtered by path prefix.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prefix": {
                        "type": "string",
                        "description": "Path prefix filter, e.g. topics/",
                        "default": "",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max notes to list (default 50, max 200)",
                        "default": 50,
                    },
                },
            },
        },
        {
            "name": "kb_stats",
            "description": "Show index statistics (note count, last indexed time, paths).",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "kb_reindex",
            "description": (
                "Rebuild the FTS index from Markdown files on disk. "
                "Call after adding/editing many notes outside Cursor."
            ),
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def kb_search(conn: sqlite3.Connection, query: str, limit: int = 8) -> dict:
    q = (query or "").strip()
    if not q:
        return {"error": "query is required"}
    limit = max(1, min(int(limit or 8), 20))

    # FTS5 trigram: quote multi-token queries as a phrase when possible
    fts_query = q.replace('"', " ")
    rows = conn.execute(
        """
        SELECT n.path, n.title, n.tags, n.body, n.mtime,
               bm25(notes_fts) AS score
        FROM notes_fts
        JOIN notes n ON n.rowid = notes_fts.rowid
        WHERE notes_fts MATCH ?
        ORDER BY score
        LIMIT ?
        """,
        (fts_query, limit),
    ).fetchall()

    # Fallback for very short queries / odd punctuation: LIKE
    if not rows and len(q) >= 1:
        like = f"%{q}%"
        rows = conn.execute(
            """
            SELECT path, title, tags, body, mtime, 0.0 AS score
            FROM notes
            WHERE title LIKE ? OR tags LIKE ? OR body LIKE ?
            ORDER BY mtime DESC
            LIMIT ?
            """,
            (like, like, like, limit),
        ).fetchall()

    results = []
    for r in rows:
        results.append(
            {
                "path": r["path"],
                "title": r["title"],
                "tags": r["tags"],
                "mtime": r["mtime"],
                "score": round(float(r["score"]), 4) if r["score"] is not None else None,
                "snippet": snippet(r["body"], q),
            }
        )
    return {"query": q, "count": len(results), "results": results}


def kb_get(conn: sqlite3.Connection, kb_root: Path, path: str) -> dict:
    rel = (path or "").strip().lstrip("/").replace("\\", "/")
    if not rel or ".." in rel.split("/"):
        return {"error": "invalid path"}
    row = conn.execute(
        "SELECT path, title, tags, body, mtime FROM notes WHERE path = ?",
        (rel,),
    ).fetchone()
    if row:
        return {
            "path": row["path"],
            "title": row["title"],
            "tags": row["tags"],
            "mtime": row["mtime"],
            "content": row["body"],
        }
    # live read fallback
    file_path = (kb_root / rel).resolve()
    if not str(file_path).startswith(str(kb_root.resolve())):
        return {"error": "path escapes kb root"}
    if not file_path.is_file():
        return {"error": f"not found: {rel}"}
    return {
        "path": rel,
        "title": file_path.stem,
        "tags": "",
        "mtime": "",
        "content": file_path.read_text(encoding="utf-8", errors="replace"),
    }


def kb_list(conn: sqlite3.Connection, prefix: str = "", limit: int = 50) -> dict:
    limit = max(1, min(int(limit or 50), 200))
    prefix = (prefix or "").strip().lstrip("/")
    if prefix:
        rows = conn.execute(
            "SELECT path, title, tags, mtime FROM notes "
            "WHERE path LIKE ? ORDER BY path LIMIT ?",
            (f"{prefix}%", limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT path, title, tags, mtime FROM notes ORDER BY path LIMIT ?",
            (limit,),
        ).fetchall()
    return {
        "count": len(rows),
        "notes": [dict(r) for r in rows],
    }


def kb_stats(conn: sqlite3.Connection, kb_root: Path, db_path: Path) -> dict:
    total = conn.execute("SELECT COUNT(*) AS c FROM notes").fetchone()["c"]
    meta = {
        r["key"]: r["value"]
        for r in conn.execute("SELECT key, value FROM meta")
    }
    return {
        "total_notes": total,
        "kb_root": str(kb_root),
        "db_path": str(db_path),
        "indexed_at": meta.get("indexed_at"),
        "meta_kb_root": meta.get("kb_root"),
    }


def call_tool(name: str, arguments: dict[str, Any]) -> Any:
    kb_root, db_path = env_paths()
    if name == "kb_reindex":
        return rebuild(kb_root, db_path)

    conn = ensure_db(db_path, kb_root)
    try:
        if name == "kb_search":
            return kb_search(conn, arguments.get("query", ""), arguments.get("limit", 8))
        if name == "kb_get":
            return kb_get(conn, kb_root, arguments.get("path", ""))
        if name == "kb_list":
            return kb_list(conn, arguments.get("prefix", ""), arguments.get("limit", 50))
        if name == "kb_stats":
            return kb_stats(conn, kb_root, db_path)
        return {"error": f"unknown tool: {name}"}
    finally:
        conn.close()


def text_result(payload: Any, is_error: bool = False) -> dict:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
        "isError": is_error,
    }


def handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC request; return response or None for notifications."""
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    # notifications (no id)
    if msg_id is None and method:
        return None

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": tool_defs()},
        }

    if method == "tools/call":
        name = params.get("name", "")
        arguments = params.get("arguments") or {}
        try:
            result = call_tool(name, arguments)
            err = isinstance(result, dict) and "error" in result
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": text_result(result, is_error=bool(err)),
            }
        except Exception as exc:  # noqa: BLE001 — surface to MCP client
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": text_result({"error": str(exc)}, is_error=True),
            }

    if method == "resources/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"resources": []}}

    if method == "prompts/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"prompts": []}}

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def read_message() -> dict[str, Any] | None:
    """Read one MCP message (Content-Length framing or newline-delimited JSON)."""
    header = b""
    while True:
        ch = sys.stdin.buffer.read(1)
        if not ch:
            return None
        header += ch
        if header.endswith(b"\r\n\r\n") or header.endswith(b"\n\n"):
            break
        # newline-delimited JSON (no headers)
        if b"\n" in header and b"Content-Length" not in header.upper() and b"{" in header:
            line = header.strip()
            if line:
                return json.loads(line.decode("utf-8"))
            header = b""

    headers = header.decode("utf-8", errors="replace")
    length = 0
    for line in headers.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        if k.strip().lower() == "content-length":
            length = int(v.strip())
            break
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def write_message(msg: dict[str, Any]) -> None:
    data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(
        f"Content-Length: {len(data)}\r\n\r\n".encode("ascii") + data
    )
    sys.stdout.buffer.flush()


def main() -> int:
    # Avoid polluting MCP stdio with accidental prints
    while True:
        try:
            msg = read_message()
        except Exception:  # noqa: BLE001
            break
        if msg is None:
            break
        resp = handle(msg)
        if resp is not None:
            write_message(resp)
        # initialized notification etc. — no response
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
