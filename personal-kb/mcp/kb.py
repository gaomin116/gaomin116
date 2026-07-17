#!/usr/bin/env python3
"""CLI helpers for personal-kb (index / search / get) without MCP."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_MCP_DIR))

from indexer import default_paths, rebuild  # noqa: E402
from server import call_tool, env_paths  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kb", description="Personal KB CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_index = sub.add_parser("index", help="Rebuild FTS index")
    p_index.add_argument("--kb", type=Path, default=None)
    p_index.add_argument("--db", type=Path, default=None)

    p_search = sub.add_parser("search", help="Search notes")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=8)

    p_get = sub.add_parser("get", help="Read a note")
    p_get.add_argument("path")

    p_list = sub.add_parser("list", help="List notes")
    p_list.add_argument("--prefix", default="")
    p_list.add_argument("--limit", type=int, default=50)

    sub.add_parser("stats", help="Show index stats")

    args = parser.parse_args(argv)
    kb_default, db_default = default_paths()

    if args.cmd == "index":
        kb = args.kb or Path(os.environ.get("PERSONAL_KB_ROOT", kb_default))
        db = args.db or Path(os.environ.get("PERSONAL_KB_DB", db_default))
        print(json.dumps(rebuild(kb, db), ensure_ascii=False, indent=2))
        return 0

    # Ensure env for call_tool
    kb, db = env_paths()
    os.environ.setdefault("PERSONAL_KB_ROOT", str(kb))
    os.environ.setdefault("PERSONAL_KB_DB", str(db))

    if args.cmd == "search":
        out = call_tool("kb_search", {"query": args.query, "limit": args.limit})
    elif args.cmd == "get":
        out = call_tool("kb_get", {"path": args.path})
    elif args.cmd == "list":
        out = call_tool("kb_list", {"prefix": args.prefix, "limit": args.limit})
    elif args.cmd == "stats":
        out = call_tool("kb_stats", {})
    else:
        parser.error(f"unknown command: {args.cmd}")
        return 2

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if isinstance(out, dict) and out.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
