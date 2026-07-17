#!/usr/bin/env python3
"""Load personal-kb config (multi-root, in-place indexing)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

ROOT_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")

DEFAULT_EXTENSIONS = [".md", ".mdx", ".txt"]
DEFAULT_EXCLUDE_DIRS = [
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
    ".cursor",
    ".idea",
    ".vscode",
    "data",
]


def package_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_db_path() -> Path:
    return package_root() / "data" / "kb.sqlite"


def default_paths_compat() -> tuple[Path, Path]:
    """Legacy (single-root) defaults used by older callers."""
    return package_root() / "kb", default_db_path()


def default_config_path() -> Path:
    env = os.environ.get("PERSONAL_KB_CONFIG")
    if env:
        return Path(env).expanduser()
    return package_root() / "config.json"


def _resolve_root_path(raw: str, base: Path) -> Path:
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = (base / p).resolve()
    else:
        p = p.resolve()
    return p


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Return normalized config with absolute root paths.

    Supported shapes:
      - config.json with roots[]
      - legacy PERSONAL_KB_ROOT / single --kb (handled by callers)
    """
    path = (config_path or default_config_path()).expanduser()
    base = package_root()

    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {}

    roots_in = data.get("roots")
    if not roots_in:
        # Legacy single-root fallback
        legacy = os.environ.get("PERSONAL_KB_ROOT")
        kb = Path(legacy).expanduser() if legacy else base / "kb"
        roots_in = [{"id": "notes", "path": str(kb)}]

    roots: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in roots_in:
        rid = str(item.get("id") or "").strip()
        raw_path = str(item.get("path") or "").strip()
        if not rid or not ROOT_ID_RE.match(rid):
            raise ValueError(f"invalid root id: {rid!r} (use letters/digits/_/-)")
        if rid in seen_ids:
            raise ValueError(f"duplicate root id: {rid}")
        if not raw_path:
            raise ValueError(f"root {rid} missing path")
        seen_ids.add(rid)
        resolved = _resolve_root_path(raw_path, base)
        roots.append(
            {
                "id": rid,
                "path": resolved,
                "description": str(item.get("description") or ""),
                "enabled": bool(item.get("enabled", True)),
            }
        )

    exts = data.get("include_extensions") or DEFAULT_EXTENSIONS
    exts = [e.lower() if e.startswith(".") else f".{e.lower()}" for e in exts]
    exclude = data.get("exclude_dir_names") or DEFAULT_EXCLUDE_DIRS

    db = Path(os.environ.get("PERSONAL_KB_DB", data.get("db_path") or default_db_path()))
    if not db.is_absolute():
        db = (base / db).resolve()
    else:
        db = db.expanduser().resolve()

    return {
        "config_path": path if path.is_file() else None,
        "roots": [r for r in roots if r["enabled"]],
        "include_extensions": exts,
        "exclude_dir_names": set(exclude),
        "db_path": db,
    }
