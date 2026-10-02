#!/usr/bin/env python3
"""PostToolUse hook: remember which declared decomposition surfaces a tool call touched.

Fires for the main agent and for subagents. Never blocks, never fails the call.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lenslog import definition, entries, state  # noqa: E402


def handle(data: dict) -> None:
    root = definition.find_root(Path(data.get("cwd") or "."))
    if root is None:
        return
    try:
        defn = definition.load(root)
    except definition.DefinitionError as e:
        print(f"[lens-log] {e}", file=sys.stderr)
        return
    hits = definition.touches(defn, data.get("tool_name", ""), data.get("tool_input") or {})
    if hits:
        state.record(data.get("session_id", ""), hits, entries.list_entries(root))


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    try:
        handle(data)
    except Exception as e:  # noqa: BLE001 — a hook must never break the session
        print(f"[lens-log] record_touch error: {e!r}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
