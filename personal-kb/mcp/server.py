#!/usr/bin/env python3
"""Minimal stdio MCP server for personal Markdown knowledge base.

Tools:
  - kb_search: FTS5 trigram search (Chinese + English friendly)
  - kb_get:    read a note by logical path (prefers live disk read)
  - kb_list:   list notes (optional prefix / limit)
  - kb_stats:  index stats + configured roots
  - kb_reindex: rebuild index from configured roots (in-place, no copy)

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

_MCP_DIR = Path(__file__).resolve().parent
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from config import load_config  # noqa: E402
from indexer import connect, init_schema, rebuild_from_config  # noqa: E402

SERVER_NAME = "personal-kb"
SERVER_VERSION = "0.2.0"
PROTOCOL_VERSION = "2024-11-05"


def current_config() -> dict[str, Any]:
    return load_config()


def ensure_db(cfg: dict[str, Any]) -> sqlite3.Connection:
    db_path: Path = cfg["db_path"]
    conn = connect(db_path)
    init_schema(conn)
    count = conn.execute("SELECT COUNT(*) AS c FROM notes").fetchone()["c"]
    if count == 0:
        conn.close()
        rebuild_from_config(cfg)
        conn = connect(db_path)
        init_schema(conn)
    return conn


def snippet(text: str, query: str, radius: int = 80) -> str:
    if not text:
        return ""
    q = query.strip()
    idx = text.lower().find(q.lower()) if q else -1
    if idx < 0:
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
                "Search the local personal knowledge base. Documents stay in their "
                "original project folders (multi-root, in-place index). "
                "Returns logical path like projects/App/docs/x.md, abs_path, snippet."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (keywords or phrase)",
                    },
                    "root": {
                        "type": "string",
                        "description": "Optional root id filter, e.g. projects",
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
                "Read a document by logical path from kb_search/kb_list "
                "(e.g. projects/MyApp/需求.md). Prefers live read from the original "
                "file on disk so you see latest edits without copying."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Logical path, e.g. notes/topics/x.md or projects/App/a.md",
                    },
                },
                "required": ["path"],
            },
        },
        {
            "name": "kb_list",
            "description": "List indexed documents, optionally filtered by path prefix or root id.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prefix": {
                        "type": "string",
                        "description": "Path prefix filter, e.g. projects/MyApp/",
                        "default": "",
                    },
                    "root": {
                        "type": "string",
                        "description": "Optional root id filter",
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
            "description": "Show index statistics and configured source roots (in-place paths).",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "kb_reindex",
            "description": (
                "Rebuild the FTS index by scanning configured roots in place. "
                "Does not copy files. Call after many add/update/delete operations."
            ),
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def kb_search(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 8,
    root: str | None = None,
) -> dict:
    q = (query or "").strip()
    if not q:
        return {"error": "query is required"}
    limit = max(1, min(int(limit or 8), 20))
    root = (root or "").strip() or None
    fts_query = q.replace('"', " ")

    sql = """
        SELECT n.path, n.root_id, n.rel_path, n.abs_path, n.title, n.tags, n.body, n.mtime,
               bm25(notes_fts) AS score
        FROM notes_fts
        JOIN notes n ON n.rowid = notes_fts.rowid
        WHERE notes_fts MATCH ?
    """
    params: list[Any] = [fts_query]
    if root:
        sql += " AND n.root_id = ?"
        params.append(root)
    sql += " ORDER BY score LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()

    if not rows and len(q) >= 1:
        like = f"%{q}%"
        if root:
            rows = conn.execute(
                """
                SELECT path, root_id, rel_path, abs_path, title, tags, body, mtime, 0.0 AS score
                FROM notes
                WHERE root_id = ? AND (title LIKE ? OR tags LIKE ? OR body LIKE ?)
                ORDER BY mtime DESC LIMIT ?
                """,
                (root, like, like, like, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT path, root_id, rel_path, abs_path, title, tags, body, mtime, 0.0 AS score
                FROM notes
                WHERE title LIKE ? OR tags LIKE ? OR body LIKE ?
                ORDER BY mtime DESC LIMIT ?
                """,
                (like, like, like, limit),
            ).fetchall()

    results = []
    for r in rows:
        results.append(
            {
                "path": r["path"],
                "root_id": r["root_id"],
                "rel_path": r["rel_path"],
                "abs_path": r["abs_path"],
                "title": r["title"],
                "tags": r["tags"],
                "mtime": r["mtime"],
                "score": round(float(r["score"]), 4) if r["score"] is not None else None,
                "snippet": snippet(r["body"], q),
            }
        )
    return {"query": q, "root": root, "count": len(results), "results": results}


def _allowed_abs_paths(cfg: dict[str, Any]) -> list[Path]:
    return [r["path"].resolve() for r in cfg["roots"]]


def _is_under_roots(file_path: Path, roots: list[Path]) -> bool:
    resolved = file_path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def kb_get(conn: sqlite3.Connection, cfg: dict[str, Any], path: str) -> dict:
    logical = (path or "").strip().lstrip("/").replace("\\", "/")
    if not logical or ".." in logical.split("/"):
        return {"error": "invalid path"}

    row = conn.execute(
        "SELECT path, root_id, rel_path, abs_path, title, tags, body, mtime FROM notes WHERE path = ?",
        (logical,),
    ).fetchone()

    roots = _allowed_abs_paths(cfg)
    file_path: Path | None = None
    if row and row["abs_path"]:
        file_path = Path(row["abs_path"])
    else:
        # Resolve logical path against configured roots: root_id/rel...
        parts = logical.split("/", 1)
        if len(parts) == 2:
            rid, rel = parts
            for root in cfg["roots"]:
                if root["id"] == rid:
                    file_path = root["path"] / rel
                    break

    # Prefer live disk content (source of truth stays in project folders)
    if file_path is not None and file_path.is_file():
        if not _is_under_roots(file_path, roots):
            return {"error": "path escapes configured roots"}
        text = file_path.read_text(encoding="utf-8", errors="replace")
        # strip front matter visually same as indexer body? keep raw for accuracy
        return {
            "path": logical,
            "root_id": row["root_id"] if row else logical.split("/", 1)[0],
            "abs_path": str(file_path.resolve()),
            "title": row["title"] if row else file_path.stem,
            "tags": row["tags"] if row else "",
            "mtime": row["mtime"] if row else "",
            "content": text,
            "source": "live-disk",
        }

    if row:
        return {
            "path": row["path"],
            "root_id": row["root_id"],
            "abs_path": row["abs_path"],
            "title": row["title"],
            "tags": row["tags"],
            "mtime": row["mtime"],
            "content": row["body"],
            "source": "index-cache",
            "warning": "original file missing; serving last indexed body",
        }

    return {"error": f"not found: {logical}"}


def kb_list(
    conn: sqlite3.Connection,
    prefix: str = "",
    limit: int = 50,
    root: str | None = None,
) -> dict:
    limit = max(1, min(int(limit or 50), 200))
    prefix = (prefix or "").strip().lstrip("/").replace("\\", "/")
    root = (root or "").strip() or None

    clauses: list[str] = []
    params: list[Any] = []
    if root:
        clauses.append("root_id = ?")
        params.append(root)
    if prefix:
        clauses.append("path LIKE ?")
        params.append(f"{prefix}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    rows = conn.execute(
        f"SELECT path, root_id, rel_path, abs_path, title, tags, mtime FROM notes "
        f"{where} ORDER BY path LIMIT ?",
        params,
    ).fetchall()
    return {"count": len(rows), "notes": [dict(r) for r in rows]}


def kb_stats(conn: sqlite3.Connection, cfg: dict[str, Any]) -> dict:
    total = conn.execute("SELECT COUNT(*) AS c FROM notes").fetchone()["c"]
    by_root = {
        r["root_id"]: r["c"]
        for r in conn.execute(
            "SELECT root_id, COUNT(*) AS c FROM notes GROUP BY root_id"
        )
    }
    meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM meta")}
    roots_meta = None
    if meta.get("roots"):
        try:
            roots_meta = json.loads(meta["roots"])
        except json.JSONDecodeError:
            roots_meta = meta["roots"]
    return {
        "total_notes": total,
        "by_root": by_root,
        "db_path": str(cfg["db_path"]),
        "config_path": str(cfg["config_path"]) if cfg.get("config_path") else None,
        "configured_roots": [
            {"id": r["id"], "path": str(r["path"]), "description": r.get("description") or ""}
            for r in cfg["roots"]
        ],
        "indexed_roots": roots_meta,
        "indexed_at": meta.get("indexed_at"),
        "mode": "in-place (no copy)",
    }


def call_tool(name: str, arguments: dict[str, Any]) -> Any:
    cfg = current_config()
    if name == "kb_reindex":
        return rebuild_from_config(cfg)

    conn = ensure_db(cfg)
    try:
        if name == "kb_search":
            return kb_search(
                conn,
                arguments.get("query", ""),
                arguments.get("limit", 8),
                arguments.get("root"),
            )
        if name == "kb_get":
            return kb_get(conn, cfg, arguments.get("path", ""))
        if name == "kb_list":
            return kb_list(
                conn,
                arguments.get("prefix", ""),
                arguments.get("limit", 50),
                arguments.get("root"),
            )
        if name == "kb_stats":
            return kb_stats(conn, cfg)
        return {"error": f"unknown tool: {name}"}
    finally:
        conn.close()


def text_result(payload: Any, is_error: bool = False) -> dict:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
        "isError": is_error,
    }


def handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

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
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tool_defs()}}

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
        except Exception as exc:  # noqa: BLE001
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
    header = b""
    while True:
        ch = sys.stdin.buffer.read(1)
        if not ch:
            return None
        header += ch
        if header.endswith(b"\r\n\r\n") or header.endswith(b"\n\n"):
            break
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
