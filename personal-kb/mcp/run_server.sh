#!/usr/bin/env bash
# Launch personal-kb MCP with paths relative to this repo (no hard-coded abs paths).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PERSONAL_KB_ROOT="${PERSONAL_KB_ROOT:-$ROOT/kb}"
export PERSONAL_KB_DB="${PERSONAL_KB_DB:-$ROOT/data/kb.sqlite}"
exec python3 "$ROOT/mcp/server.py"
